"""
hv_frozen.py — CANONICAL FROZEN HeartVector pipeline (median-beat generation).

This is the single source of truth for the Reversible-Perturbation arm. It bundles,
VERBATIM, the frozen artifacts that produced the published Chapman/CODE results:

  1. Clock1DCNN               — the trained architecture (strict state_dict match to
                                clock_{whole,p,pr,qrs,stt}.pt; bare state_dicts, NO amu/asd).
  2. subsystem_extractor      — median-beat + 4 subsystem masks from a raw 12-lead ECG
                                (NeuroKit2 DWT delineation on lead II). Constants VERBATIM.
  3. AMU/ASD                  — age standardization from the PTB-XL TRAIN split
                                (cohort_manifest, n=17090): pred = net(x)*ASD + AMU.
  4. score_frozen             — adapt_coef -> per-phase z -> A / q / D4 / D3_dropP / D3_noAV,
                                using FROZEN_DISAGREEMENT_DEFINITIONS_RC2. VALIDATED bit-exact
                                (max|Δ|=0 on adapted/z/A/D) against 44,832 stored Chapman rows.

NOTHING here refits or recalibrates any clock, calibration function, contrast basis,
covariance, or standardization constant. All perturbation arms import this module unchanged.

Clock name map (frozen phase <- historical checkpoint):
    whole/global <- clock_whole.pt      P   <- clock_p.pt
    AV           <- clock_pr.pt         QRS <- clock_qrs.pt      STT <- clock_stt.pt
"""
import os, json, warnings
import numpy as np
warnings.filterwarnings("ignore")

# ============================ AGE STANDARDIZATION (FROZEN) ============================
# PTB-XL train split (cohort_manifest, split=='train', n=17090). train_clocks_medianbeat.py
# uses amu=tr.age.mean(); asd=tr.age.std()  (pandas default ddof=1).
AMU = 59.64406085430077
ASD = 16.282862331239707

# ============================ MEDIAN-BEAT EXTRACTOR (VERBATIM) ========================
# From subsystem_extractor.py (electrical-body-clock repo). These FB/BOUNDS are the
# MEDIAN-BEAT constants and DIFFER from the (superseded) strip pipeline — do not swap.
import wfdb, neurokit2 as nk
FS = 500; PRE, POST = 150, 300; L = PRE + POST; R_IDX = PRE
FB      = dict(P_on=-110, P_off=-50, R_on=-25, R_off=25, T_off=200)
BOUNDS  = dict(P_on=(-115,-45), P_off=(-75,-20), R_on=(-40,-6), R_off=(16,80), T_off=(95,235))

def _median_offset(fid_idx, rpeaks):
    fid = np.asarray(fid_idx, float); n = min(len(fid), len(rpeaks))
    if n == 0: return np.nan
    d = fid[:n] - rpeaks[:n]; d = d[~np.isnan(d)]
    d = d[(d > -0.4*FS) & (d < 0.6*FS)]
    return float(np.median(d)) if len(d) else np.nan

def extract_from_signal(sig12, fs_in=500):
    """sig12: (N,12) raw 12-lead in FROZEN canonical lead order, any sampling rate.
    Resamples to 500 Hz if needed, then median-beat + masks. Returns (data|None, qa)."""
    qa = {}
    sig12 = np.asarray(sig12, float)
    if fs_in != FS:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(FS, int(fs_in)); sig12 = resample_poly(sig12, up=FS//g, down=int(fs_in)//g, axis=0)
    N = sig12.shape[0]
    try:
        clean = nk.ecg_clean(sig12[:,1], sampling_rate=FS)
        rpeaks = nk.ecg_peaks(clean, sampling_rate=FS)[1]["ECG_R_Peaks"]
    except Exception as e:
        qa.update(ok=0, reason=f"rpeaks:{type(e).__name__}"); return None, qa
    qa["n_rpeaks"] = int(len(rpeaks))
    if len(rpeaks) < 3: qa.update(ok=0, reason="too_few_rpeaks"); return None, qa
    try:
        w = nk.ecg_delineate(clean, rpeaks=rpeaks, sampling_rate=FS, method="dwt")[1]; deline_ok=1
    except Exception:
        w = {}; deline_ok = 0
    raw = {"P_on":_median_offset(w.get("ECG_P_Onsets",[]),rpeaks),
           "P_off":_median_offset(w.get("ECG_P_Offsets",[]),rpeaks),
           "R_on":_median_offset(w.get("ECG_R_Onsets",[]),rpeaks),
           "R_off":_median_offset(w.get("ECG_R_Offsets",[]),rpeaks),
           "T_off":_median_offset(w.get("ECG_T_Offsets",[]),rpeaks)}
    off = {}; clamp = {}
    for k,(lo,hi) in BOUNDS.items():
        v = raw[k]
        if np.isnan(v): off[k]=FB[k]; clamp[k]=2
        else: cv=min(max(v,lo),hi); off[k]=cv; clamp[k]=int(cv!=v)
    off["P_off"] = min(off["P_off"], off["R_on"]-2)
    off["P_on"]  = min(off["P_on"],  off["P_off"]-4)
    off["R_off"] = max(off["R_off"], off["R_on"]+8)
    off["T_off"] = max(off["T_off"], off["R_off"]+20)
    beats = [sig12[r-PRE:r+POST,:] for r in rpeaks if r-PRE>=0 and r+POST<=N]
    qa["n_beats_used"] = len(beats)
    if len(beats) < 2: qa.update(ok=0, reason="too_few_full_beats"); return None, qa
    med = np.median(np.stack(beats,0), axis=0).astype(np.float32)
    def win(a,b):
        lo,hi = int(round(R_IDX+a)), int(round(R_IDX+b))
        lo,hi = max(0,min(lo,L-1)), max(1,min(hi,L))
        return (lo, hi if hi>lo else lo+1)
    wins = dict(P=win(off["P_on"],off["P_off"]), PR=win(off["P_off"],off["R_on"]),
                QRS=win(off["R_on"],off["R_off"]), STT=win(off["R_off"],off["T_off"]))
    masks = np.zeros((4,L), np.float32)
    for i,k in enumerate(["P","PR","QRS","STT"]):
        masks[i, wins[k][0]:wins[k][1]] = 1.0
    qa.update(ok=1, reason="", deline_ok=deline_ok, n_beats=len(beats),
              **{f"clamp_{k}":clamp[k] for k in clamp},
              **{f"off_{k}":float(off[k]) for k in off})
    return dict(median_beat=med, masks=masks, wins=wins, offsets=off, raw_offsets=raw), qa

def extract_record(path, fs_in=None):
    """wfdb record path (no extension) -> (data|None, qa). Reads canonical 12-lead."""
    qa = dict(path=path)
    try:
        rec = wfdb.rdrecord(path); sig = np.asarray(rec.p_signal, float)
        fs = int(getattr(rec,"fs",500) or 500)
    except Exception as e:
        qa.update(ok=0, reason=f"read:{type(e).__name__}"); return None, qa
    if sig.ndim != 2 or sig.shape[1] < 12:
        qa.update(ok=0, reason="shape"); return None, qa
    data, qa2 = extract_from_signal(sig[:, :12], fs_in=fs if fs_in is None else fs_in)
    qa.update(qa2); return data, qa

def staff_to_canonical(rec):
    """STAFF III stores 9 leads in order [V1..V6, I, II, III] at 1000 Hz (aVR/aVL/aVF absent).
    Reconstruct canonical 12-lead I,II,III,aVR,aVL,aVF,V1..V6; augmented limb leads derived via
    Goldberger (aVR=-(I+II)/2, aVL=(I-III)/2, aVF=(II+III)/2). Returns (N,12) float32.
    Verified: Einthoven II=I+III residual ~1e-3 on STAFF data (correct lead identification)."""
    names=[str(s).strip().upper() for s in rec.sig_name]
    idx={n:i for i,n in enumerate(names)}
    need=["I","II","III","V1","V2","V3","V4","V5","V6"]
    miss=[l for l in need if l not in idx]
    if miss: raise ValueError(f"STAFF record missing leads {miss}; have {names}")
    sig=np.asarray(rec.p_signal, float)
    I=sig[:,idx["I"]]; II=sig[:,idx["II"]]; III=sig[:,idx["III"]]
    aVR=-(I+II)/2.0; aVL=(I-III)/2.0; aVF=(II+III)/2.0
    V=[sig[:,idx[f"V{k}"]] for k in range(1,7)]
    return np.column_stack([I,II,III,aVR,aVL,aVF]+V).astype(np.float32)

def masked_inputs(data):
    """(5,12,L): index 0 = WHOLE (unmasked) beat; 1..4 = P,PR,QRS,STT masked beats."""
    med = data["median_beat"].T                       # (12, L)
    sub = med[None,:,:] * data["masks"][:,None,:]      # (4,12,L)
    return np.concatenate([med[None,:,:], sub], axis=0).astype(np.float32)  # (5,12,L)

# ============================ CLOCK ARCHITECTURE (VERBATIM) ===========================
import torch, torch.nn as nn
class Clock1DCNN(nn.Module):
    """Frozen age regressor from a (12,L) masked median beat. Matches clock_*.pt exactly."""
    def __init__(self, in_ch=12):
        super().__init__()
        def blk(i,o,k=7,s=2):
            return nn.Sequential(nn.Conv1d(i,o,k,s,k//2), nn.BatchNorm1d(o), nn.ReLU(),
                                 nn.Conv1d(o,o,3,1,1), nn.BatchNorm1d(o), nn.ReLU())
        self.net=nn.Sequential(blk(in_ch,32), blk(32,64), blk(64,128), blk(128,128),
                               nn.AdaptiveAvgPool1d(1), nn.Flatten())
        self.head=nn.Sequential(nn.Linear(128,64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64,1))
    def forward(self,x): return self.head(self.net(x)).squeeze(-1)

# frozen phase name -> checkpoint file basename (in MODELS_DIR/{file}/best.pt OR MODELS_DIR/{file}.pt)
CLOCK_FILE = {"global":"whole", "P":"p", "AV":"pr", "QRS":"qrs", "STT":"stt"}
CLOCK_ORDER = ["global","P","AV","QRS","STT"]
_MASK_ROW = {"global":0, "P":1, "AV":2, "QRS":3, "STT":4}   # row into masked_inputs()

def load_clocks(models_dir, device="cpu"):
    """Load all 5 frozen Clock1DCNN. Accepts either {name}/best.pt or clock_{file}.pt layouts."""
    nets = {}
    for phase, fb in CLOCK_FILE.items():
        cands = [os.path.join(models_dir, phase, "best.pt"),
                 os.path.join(models_dir, phase.upper(), "best.pt"),
                 os.path.join(models_dir, fb, "best.pt"),
                 os.path.join(models_dir, fb.upper(), "best.pt"),
                 os.path.join(models_dir, f"clock_{fb}.pt")]
        p = next((c for c in cands if os.path.exists(c)), None)
        if p is None: raise FileNotFoundError(f"no checkpoint for phase {phase} in {models_dir} (tried {cands})")
        sd = torch.load(p, map_location=device, weights_only=True)
        if isinstance(sd, dict) and "state" in sd: sd = sd["state"]      # tolerate wrapped
        net = Clock1DCNN().to(device)
        miss, unexp = net.load_state_dict(sd, strict=True)               # STRICT — fail loud
        net.eval(); nets[phase] = net
    return nets

@torch.no_grad()
def infer_clocks(inputs_5xCxL, nets, device="cpu", batch=512):
    """inputs_5xCxL: (n,5,12,L) stacked masked_inputs per record.
    Returns dict phase -> (n,) predicted age in YEARS (net output * ASD + AMU)."""
    X = np.asarray(inputs_5xCxL, np.float32); n = len(X)
    preds = {ph: np.full(n, np.nan, np.float32) for ph in CLOCK_ORDER}
    for ph in CLOCK_ORDER:
        row = _MASK_ROW[ph]; net = nets[ph]
        for i in range(0, n, batch):
            xb = torch.from_numpy(X[i:i+batch, row]).to(device)          # (b,12,L)
            preds[ph][i:i+batch] = net(xb).cpu().numpy() * ASD + AMU
    return preds

# ============================ FROZEN A / q / D SCORER (VALIDATED) =====================
_DEFS = None
def load_defs(defs_path):
    global _DEFS
    _DEFS = json.load(open(defs_path)); return _DEFS

PHASE4 = ["P","AV","QRS","STT"]
def _design(age, sex):
    age=np.asarray(age,float); sex=np.asarray(sex,float); a=(age-50.0)/10.0
    return np.column_stack([np.ones_like(a), a, a*a, sex, sex*a])

def score_frozen(pred_by_phase, age, sex, defs=None):
    """pred_by_phase: dict with pred ages for 'P','AV','QRS','STT' (+ optional 'global').
    age: years; sex: 1=female,0=male (frozen coding). Returns dict of score arrays.
    Reproduces stored Chapman adapted_*/z_*/A/D bit-exact (validated max|Δ|=0)."""
    d = defs or _DEFS
    ADAPT = d["adapt_coef"]; CALF = d["calibration_functions"]
    age=np.asarray(age,float); sex=np.asarray(sex,float)
    out={}; Z=[]
    for ph in PHASE4:
        ad = np.polyval(ADAPT[ph], np.asarray(pred_by_phase[ph],float)); out[f"adapted_{ph}"]=ad
        X=_design(age,sex); cal=CALF[ph]
        m=X@np.asarray(cal["beta_mean"],float)
        sig=np.maximum(np.exp(0.5*(X@np.asarray(cal["beta_logvar"],float))), cal["min_sigma"])
        z=(ad-m)/sig; out[f"z_{ph}"]=z; Z.append(z)
    if "global" in pred_by_phase:
        out["adapted_global"]=np.polyval(ADAPT["global"], np.asarray(pred_by_phase["global"],float))
    Z=np.column_stack(Z)
    A=Z@(np.ones(4)/2.0); out["A"]=A
    Ad=d["A_definitions"]["A4"]; out["A_std"]=(A-Ad["center"])/Ad["scale"]
    def _D(name, phases, zcols):
        s=d["scores"][name]; C=np.array(s["contrast_C"]); Sinv=np.array(s["Sigma_q_inv"]); mq=np.array(s["mu_q"])
        Zk=np.column_stack([out[f"z_{p}"] for p in zcols]); q=Zk@C.T-mq
        D=np.sqrt(np.einsum("ni,ij,nj->n",q,Sinv,q))
        return D, (D-s["D_std_center"])/s["D_std_scale"], q
    D,Dstd,q = _D("D4", PHASE4, PHASE4)
    out["D"]=D; out["D_std"]=Dstd
    out["q1"],out["q2"],out["q3"]=q[:,0],q[:,1],q[:,2]
    out["D3_dropP"],out["D3_dropP_std"],_ = _D("D3_dropP",["AV","QRS","STT"],["AV","QRS","STT"])
    out["D3_noAV"],out["D3_noAV_std"],_   = _D("D3_noAV",["P","QRS","STT"],["P","QRS","STT"])
    return out
