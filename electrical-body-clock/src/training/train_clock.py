"""Phase 2 — train one age-regression clock (global or a subsystem).

A compact 1D ResNet reads a 12-lead 10s strip (12 x 5000). For a subsystem
clock the strip is multiplied by that subsystem's per-sample mask BEFORE the
network sees it, so the model only ever observes the P / PR-seg / QRS / ST-T
samples (the rest is zeroed) — rhythm within the masked region is preserved.
The global clock sees the unmasked strip.

Usage (env vars):
  CLOCK   = global | P | PR | QRS | STT     (which mask; 'global' = none)
  EPOCHS  = 40
  BATCH   = 128
  LR      = 2e-3
Reads /data/proc/{X_strip.npy, M_mask.npy, labels.parquet}.
Writes /data/models/{CLOCK}/best.pt and per-ECG predictions for val+test,
plus a receipt to ./out/.
"""
import os, sys, time, json
import numpy as np, pandas as pd
import torch, torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

PROC = "/data/proc"; MODELS = "/data/models"; OUT = "./out"
os.makedirs(OUT, exist_ok=True)
CLOCK  = os.environ.get("CLOCK", "global")
EPOCHS = int(os.environ.get("EPOCHS", 40))
BATCH  = int(os.environ.get("BATCH", 128))
LR     = float(os.environ.get("LR", 2e-3))
SEED   = int(os.environ.get("SEED", 0))
MASK_IDX = {"P": 0, "PR": 1, "QRS": 2, "STT": 3}
DEV = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(SEED); np.random.seed(SEED)
def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ---------------- model: 1D ResNet ----------------
class BasicBlock1d(nn.Module):
    def __init__(self, cin, cout, stride=1):
        super().__init__()
        self.c1 = nn.Conv1d(cin, cout, 7, stride, 3, bias=False); self.b1 = nn.BatchNorm1d(cout)
        self.c2 = nn.Conv1d(cout, cout, 7, 1, 3, bias=False);      self.b2 = nn.BatchNorm1d(cout)
        self.act = nn.ReLU(inplace=True)
        self.down = None
        if stride != 1 or cin != cout:
            self.down = nn.Sequential(nn.Conv1d(cin, cout, 1, stride, bias=False), nn.BatchNorm1d(cout))
    def forward(self, x):
        idt = x if self.down is None else self.down(x)
        x = self.act(self.b1(self.c1(x)))
        x = self.b2(self.c2(x))
        return self.act(x + idt)

class ResNet1d(nn.Module):
    def __init__(self, cin=12, base=32, nblocks=(2,2,2,2)):
        super().__init__()
        self.stem = nn.Sequential(nn.Conv1d(cin, base, 15, 2, 7, bias=False),
                                  nn.BatchNorm1d(base), nn.ReLU(inplace=True), nn.MaxPool1d(3,2,1))
        chs = [base, base*2, base*4, base*8]; layers = []; cprev = base
        for c, nb in zip(chs, nblocks):
            layers.append(BasicBlock1d(cprev, c, stride=2))
            for _ in range(nb-1): layers.append(BasicBlock1d(c, c, 1))
            cprev = c
        self.body = nn.Sequential(*layers)
        self.head = nn.Sequential(nn.AdaptiveAvgPool1d(1), nn.Flatten(),
                                  nn.Dropout(0.3), nn.Linear(cprev, 1))
    def forward(self, x): return self.head(self.body(self.stem(x))).squeeze(-1)


def load_split():
    X = np.load(f"{PROC}/X_strip.npy", mmap_mode="r")           # (N,12,5000) f16
    M = np.load(f"{PROC}/M_mask.npy", mmap_mode="r")            # (N,4,5000) u8
    lab = pd.read_parquet(f"{PROC}/labels.parquet").reset_index(drop=True)
    assert len(lab) == X.shape[0], (len(lab), X.shape)
    return X, M, lab

def make_tensors(X, M, idx, clock):
    """Materialise a (n,12,5000) float32 tensor for the given row indices,
    applying the subsystem mask if clock != global."""
    xb = np.asarray(X[idx], dtype=np.float32)                  # (n,12,5000)
    if clock != "global":
        m = np.asarray(M[idx, MASK_IDX[clock]], dtype=np.float32)[:, None, :]  # (n,1,5000)
        xb = xb * m
    return torch.from_numpy(xb)

def main():
    t0 = time.time()
    log(f"CLOCK={CLOCK} DEV={DEV} epochs={EPOCHS} batch={BATCH} lr={LR}")
    X, M, lab = load_split()
    age = lab.age.values.astype(np.float32)
    tr = np.where(lab.split.values == "train")[0]
    va = np.where(lab.split.values == "val")[0]
    te = np.where(lab.split.values == "test")[0]
    log(f"n: train={len(tr)} val={len(va)} test={len(te)}")

    # age standardisation (fit on train)
    amu, asd = float(age[tr].mean()), float(age[tr].std())
    def yz(a): return (a - amu) / asd
    def yinv(z): return z * asd + amu

    net = ResNet1d().to(DEV)
    opt = torch.optim.AdamW(net.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=LR, epochs=EPOCHS,
                steps_per_epoch=int(np.ceil(len(tr)/BATCH)))
    lossf = nn.SmoothL1Loss()

    ytr = torch.from_numpy(yz(age[tr]))
    # pre-materialise val/test once (fits in RAM: ~2k x 12 x 5000 x4 = 0.5GB each)
    Xva = make_tensors(X, M, va, CLOCK); yva = age[va]
    Xte = make_tensors(X, M, te, CLOCK); yte = age[te]

    def evaluate(Xe, ye):
        net.eval(); preds = []
        with torch.no_grad():
            for i in range(0, len(Xe), 256):
                xb = Xe[i:i+256].to(DEV)
                preds.append(yinv(net(xb).cpu().numpy()))
        p = np.concatenate(preds)
        mae = float(np.mean(np.abs(p - ye))); 
        r2 = float(1 - np.sum((p-ye)**2)/np.sum((ye-ye.mean())**2))
        return mae, r2, p

    best_mae = 1e9; best_state = None; patience = 0
    rng = np.random.default_rng(SEED)
    for ep in range(EPOCHS):
        net.train(); order = rng.permutation(len(tr)); ep_loss = 0
        for i in range(0, len(tr), BATCH):
            bidx = tr[order[i:i+BATCH]]
            xb = make_tensors(X, M, bidx, CLOCK).to(DEV)
            yb = ytr[order[i:i+BATCH]].to(DEV)
            opt.zero_grad(); out = net(xb); loss = lossf(out, yb)
            loss.backward(); opt.step(); sched.step()
            ep_loss += loss.item()*len(bidx)
        vmae, vr2, _ = evaluate(Xva, yva)
        log(f"  ep{ep:02d} loss={ep_loss/len(tr):.4f} val_MAE={vmae:.3f} val_R2={vr2:.3f}")
        if vmae < best_mae - 1e-3:
            best_mae = vmae; best_state = {k: v.cpu().clone() for k,v in net.state_dict().items()}; patience = 0
        else:
            patience += 1
            if patience >= 8: log(f"  early stop @ ep{ep}"); break

    net.load_state_dict(best_state)
    vmae, vr2, vp = evaluate(Xva, yva)
    tmae, tr2, tp = evaluate(Xte, yte)
    log(f"BEST val_MAE={vmae:.3f} R2={vr2:.3f} | test_MAE={tmae:.3f} R2={tr2:.3f}")

    od = f"{MODELS}/{CLOCK}"; os.makedirs(od, exist_ok=True)
    torch.save({"state": best_state, "amu": amu, "asd": asd, "clock": CLOCK}, f"{od}/best.pt")
    # per-ECG predictions for val+test (for the disease matrix)
    pred = pd.DataFrame({
        "ecg_id": np.concatenate([lab.ecg_id.values[va], lab.ecg_id.values[te]]),
        "split": ["val"]*len(va) + ["test"]*len(te),
        "age": np.concatenate([yva, yte]),
        f"pred_{CLOCK}": np.concatenate([vp, tp]),
    })
    pred.to_parquet(f"{od}/pred.parquet")
    receipt = {"clock": CLOCK, "val_MAE": round(vmae,3), "val_R2": round(vr2,3),
               "test_MAE": round(tmae,3), "test_R2": round(tr2,3),
               "amu": round(amu,2), "asd": round(asd,2), "epochs_ran": ep+1,
               "seconds": round(time.time()-t0)}
    json.dump(receipt, open(f"{OUT}/train_receipt_{CLOCK}.json", "w"), indent=2)
    log(f"RECEIPT: {receipt}")

if __name__ == "__main__":
    main()
