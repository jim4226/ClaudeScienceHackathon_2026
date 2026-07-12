"""
subsystem_extractor.py — The Electrical Body Clock
Extract four non-overlapping electrical-subsystem windows from a 12-lead ECG.

  P   window : atrial activity              (P_onset  -> P_offset)
  PR  window : AV conduction (PR segment)   (P_offset -> QRS_onset)   [isoelectric delay]
  QRS window : ventricular depolarization   (QRS_onset-> QRS_offset)
  STT window : repolarization               (QRS_offset-> T_offset)

Method: NeuroKit2 DWT delineation on lead II, element-wise fiducial->R-peak pairing,
physiological clamping + ordering, median-beat construction across all detected beats.
Returns a median beat (L x 12) plus four boolean masks -> segment-masked model inputs.
"""
import numpy as np, wfdb, neurokit2 as nk, warnings
warnings.filterwarnings("ignore")

FS = 500; PRE, POST = 150, 300; L = PRE + POST; R_IDX = PRE
FB      = dict(P_on=-110, P_off=-50, R_on=-25, R_off=25, T_off=200)
BOUNDS  = dict(P_on=(-115,-45), P_off=(-75,-20), R_on=(-40,-6), R_off=(16,80), T_off=(95,235))

def _median_offset(fid_idx, rpeaks):
    fid = np.asarray(fid_idx, float); n = min(len(fid), len(rpeaks))
    if n == 0: return np.nan
    d = fid[:n] - rpeaks[:n]; d = d[~np.isnan(d)]
    d = d[(d > -0.4*FS) & (d < 0.6*FS)]
    return float(np.median(d)) if len(d) else np.nan

def extract_record(path):
    """path: wfdb record path (no extension). Returns (data|None, qa dict)."""
    qa = dict(path=path)
    try:
        sig12 = wfdb.rdrecord(path).p_signal.astype(float)
    except Exception as e:
        qa.update(ok=0, reason=f"read:{type(e).__name__}"); return None, qa
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
    qa.update(ok=1, reason="", deline_ok=deline_ok,
              **{f"clamp_{k}":clamp[k] for k in clamp},
              **{f"dur_{k}":round((wins[k][1]-wins[k][0])/FS*1000,0) for k in wins})
    return dict(median_beat=med, masks=masks, wins=wins, offsets=off), qa

def masked_inputs(data):
    """(4,12,L) float32: for each subsystem, the median beat with only that window kept."""
    med = data["median_beat"].T            # (12, L)
    return (med[None,:,:] * data["masks"][:,None,:]).astype(np.float32)
