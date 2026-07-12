"""
Train four segment-masked 1D-CNN electrical-age clocks for The Electrical Body Clock (Act I).

Each clock sees the SAME (12 x L) median beat, gated by ONE subsystem mask
(p / pr / qrs / stt). Target = chronological age. Identical architecture per clock;
only the visible electrical window differs. Also trains a WHOLE-BEAT baseline (no mask)
= the conventional single ECG-age model, so we can show decomposition adds information.

Outputs per model: predicted age (test), MAE, and the age-gap (pred - chrono) used
downstream for the disease-substrate specificity matrix.
"""
import os, json, numpy as np, pandas as pd, h5py, time
import torch, torch.nn as nn
from torch.utils.data import Dataset, DataLoader

WIN = "drive_staging/ptbxl/windows"
MANIFEST = "drive_staging/ptbxl/cohort_manifest.csv"
OUT = "drive_staging/ptbxl/models"; os.makedirs(OUT, exist_ok=True)
DEV = "cuda" if torch.cuda.is_available() else "cpu"
MASK_ORDER = ["p_mask","pr_mask","qrs_mask","stt_mask"]   # index into masks.h5 (4,L)
SUBSYS = {"p":"Atrial (P)","pr":"AV conduction (PR)","qrs":"Ventricular depol. (QRS)","stt":"Repolarisation (ST-T)","whole":"Whole beat (baseline)"}


# ---- load ALL beats + masks into RAM once (small: ~21k x 12 x 600 f16 ~300MB) ----
_CACHE = {}
def _load_all():
    if _CACHE: return _CACHE
    with h5py.File(f"{WIN}/beats.h5","r") as b, h5py.File(f"{WIN}/masks.h5","r") as m:
        ids=list(b.keys())
        beats=np.stack([np.asarray(b[e],np.float32) for e in ids])     # (N,12,L)
        masks=np.stack([np.asarray(m[e],np.float32) for e in ids])     # (N,4,L)
    _CACHE["ids"]={int(e):i for i,e in enumerate(ids)}
    _CACHE["beats"]=beats; _CACHE["masks"]=masks
    return _CACHE

class ECGWindows(Dataset):
    """In-RAM dataset; applies one subsystem mask (or none)."""
    def __init__(self, ecg_ids, ages, subsystem):
        C=_load_all(); idmap=C["ids"]
        rows=[(idmap[int(e)],a,int(e)) for e,a in zip(ecg_ids,ages) if int(e) in idmap]
        self.idx=np.array([r[0] for r in rows])
        self.ages=np.array([r[1] for r in rows],np.float32)
        self.ecg_ids=[r[2] for r in rows]
        self.subsystem=subsystem
        self.beats=C["beats"]; self.masks=C["masks"]
        self.mi=None if subsystem=="whole" else MASK_ORDER.index(subsystem+"_mask")
    def __len__(self): return len(self.idx)
    def __getitem__(self, i):
        j=self.idx[i]; beat=self.beats[j]
        x=beat if self.mi is None else beat*self.masks[j,self.mi][None,:]
        return torch.from_numpy(x.copy()), torch.tensor(self.ages[i])


class Clock1DCNN(nn.Module):
    """Small 1D CNN (no transformer) — age regressor from a (12,L) masked beat."""
    def __init__(self, in_ch=12):
        super().__init__()
        def blk(i,o,k=7,s=2):
            return nn.Sequential(nn.Conv1d(i,o,k,s,k//2), nn.BatchNorm1d(o), nn.ReLU(),
                                 nn.Conv1d(o,o,3,1,1), nn.BatchNorm1d(o), nn.ReLU())
        self.net=nn.Sequential(blk(in_ch,32), blk(32,64), blk(64,128), blk(128,128),
                               nn.AdaptiveAvgPool1d(1), nn.Flatten())
        self.head=nn.Sequential(nn.Linear(128,64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64,1))
    def forward(self,x): return self.head(self.net(x)).squeeze(-1)


def run_one(subsystem, tr, va, te, epochs=30, bs=256, lr=1e-3, seed=0):
    torch.manual_seed(seed); np.random.seed(seed)
    dl=lambda ds,sh: DataLoader(ds,batch_size=bs,shuffle=sh,num_workers=0,drop_last=False)
    dtr,dva,dte=dl(ECGWindows(tr.ecg_id,tr.age,subsystem),True),\
                dl(ECGWindows(va.ecg_id,va.age,subsystem),False),\
                dl(ECGWindows(te.ecg_id,te.age,subsystem),False)
    # standardize target (age) using TRAIN stats; invert for reporting
    amu=float(tr.age.mean()); asd=float(tr.age.std())
    model=Clock1DCNN().to(DEV); opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=1e-4)
    sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,epochs); lossf=nn.SmoothL1Loss()
    best_va=1e9; best_state=None
    for ep in range(epochs):
        model.train()
        for x,y in dtr:
            x=x.to(DEV); yz=((y-amu)/asd).to(DEV); opt.zero_grad()
            loss=lossf(model(x),yz); loss.backward(); opt.step()
        sched.step()
        # val MAE (invert z-score to years)
        model.eval(); ae=[]
        with torch.no_grad():
            for x,y in dva:
                p=model(x.to(DEV)).cpu().numpy()*asd+amu; ae.append(np.abs(p-y.numpy()))
        va_mae=float(np.concatenate(ae).mean())
        if va_mae<best_va: best_va=va_mae; best_state={k:v.cpu().clone() for k,v in model.state_dict().items()}
    # test with best
    model.load_state_dict(best_state); model.eval()
    ids=[]; preds=[]; ys=[]
    with torch.no_grad():
        ds=ECGWindows(te.ecg_id,te.age,subsystem)
        for i in range(len(ds)):
            x,y=ds[i]; p=float(model(x.unsqueeze(0).to(DEV)).cpu())*asd+amu
            ids.append(ds.ecg_ids[i]); preds.append(p); ys.append(float(y))
    res=pd.DataFrame({"ecg_id":ids,"age":ys,f"pred_{subsystem}":preds})
    res[f"gap_{subsystem}"]=res[f"pred_{subsystem}"]-res["age"]
    te_mae=float((res[f"pred_{subsystem}"]-res["age"]).abs().mean())
    torch.save(best_state,f"{OUT}/clock_{subsystem}.pt")
    return dict(subsystem=subsystem,val_mae=round(best_va,3),test_mae=round(te_mae,3),n_test=len(res)), res


def main(epochs=30, subset=None):
    m=pd.read_csv(MANIFEST)
    if subset:
        m=pd.concat([g.head(subset) for _,g in m.groupby("split")], ignore_index=True)
    tr,va,te=m[m.split=="train"],m[m.split=="val"],m[m.split=="test"]
    print(f"device={DEV} | train={len(tr)} val={len(va)} test={len(te)} | epochs={epochs}",flush=True)
    summary=[]; merged=None
    for sub in ["whole"]+[s.split("_")[0] for s in MASK_ORDER]:
        t0=time.time(); stat,res=run_one(sub,tr,va,te,epochs=epochs)
        stat["sec"]=round(time.time()-t0); summary.append(stat)
        print(f"  {sub:5s}: val_MAE={stat['val_mae']} test_MAE={stat['test_mae']} ({stat['sec']}s)",flush=True)
        cols=["ecg_id","age",f"pred_{sub}",f"gap_{sub}"]
        merged=res[cols] if merged is None else merged.merge(res[["ecg_id",f"pred_{sub}",f"gap_{sub}"]],on="ecg_id")
    pd.DataFrame(summary).to_csv(f"{OUT}/clock_summary.csv",index=False)
    merged.to_csv(f"{OUT}/test_predictions.csv",index=False)
    print("SAVED clock_summary.csv + test_predictions.csv",flush=True)
    return summary

if __name__=="__main__":
    import sys
    ep=int(sys.argv[1]) if len(sys.argv)>1 else 30
    sub=int(sys.argv[2]) if len(sys.argv)>2 else None
    main(epochs=ep, subset=sub)
