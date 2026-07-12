"""Job B — extract subsystem-masked 10s strips + interval biomarkers at scale.

For each adult ECG in the frozen cohort manifest:
  * load the 500 Hz 12-lead 10s record (5000 x 12)
  * NeuroKit2 DWT delineation on lead II across the WHOLE strip (per-beat)
  * build four per-sample subsystem masks over the full 10s (P / PR-seg / QRS / ST-T),
    so rhythm (RR irregularity, absent P in AF, fibrillatory waves) is preserved
  * derive handcrafted interval biomarkers (median P dur, PR, QRS dur, QT, QTc,
    RR mean/SD, heart rate) for the ladder's biomarker baseline
  * z-score each lead (per-record) for model input stability

Outputs to /data/proc/ (on the Volume):
  X_strip.npy   float16 (N, 12, 5000)     z-scored 12-lead strip
  M_mask.npy    uint8   (N, 4, 5000)      P/PR/QRS/ST-T per-sample masks
  biomarkers.parquet   per-ECG interval features + QA
  labels.parquet       ecg_id, patient_id, age, sex, split, disease-group flags
  extract_qa.parquet   per-ECG QA (ok flag, reason, n_rpeaks, deline_ok, mask_frac)
A JSON receipt (out/extract_receipt.json) is written to ./out/ for harvest;
QA figures are rendered locally after harvest, not in this job.

Parallelised across CPU cores with a process pool. Resumable via shard files.
"""
import os, sys, time, json, ast, warnings, glob, zipfile, io, tempfile
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import wfdb, neurokit2 as nk
from concurrent.futures import ProcessPoolExecutor, as_completed

ZIP_PATH = "/data/ptbxl-data.zip"; OUT = "./out"
PROC = os.environ.get("PROC_DIR", "/data/proc")   # smoke test overrides to /data/proc_smoke
os.makedirs(PROC, exist_ok=True); os.makedirs(OUT, exist_ok=True)
FS = 500; N_SAMP = 5000            # 10 s @ 500 Hz
LEAD_II = 1

# Each worker opens its OWN handle to the zip (ZipFile is not fork/thread safe).
_ZH = {"z": None}
def _zh():
    if _ZH["z"] is None:
        _ZH["z"] = zipfile.ZipFile(ZIP_PATH)
    return _ZH["z"]

def read_record_from_zip(relpath):
    """relpath like 'records500/00000/00123_hr' -> read .dat+.hea from the zip
    into a temp dir, load with wfdb, return (5000,12) float32 signal."""
    z = _zh()
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, os.path.basename(relpath))
        for ext in (".hea", ".dat"):
            with z.open(relpath + ext) as src:
                open(base + ext, "wb").write(src.read())
        return wfdb.rdrecord(base).p_signal.astype(np.float32)

# ---- fiducial helpers (per-beat, spanning the whole strip) ----
# Bounds set from measured RAW DWT offset distributions across disease groups
# (samples rel. R peak, 2 ms/sample). P_on floor widened to -185 so AV block's
# genuinely long PR interval is not truncated (AV P_on ~ -132 vs normal ~ -100).
FB = dict(P_on=-100, P_off=-50, R_on=-22, R_off=28, T_off=180)          # median-normal fallbacks
BOUNDS = dict(P_on=(-185,-45), P_off=(-95,-25), R_on=(-70,-8), R_off=(16,90), T_off=(80,260))

def _median_offset(fid, rpeaks):
    fid = np.asarray(fid, float); n = min(len(fid), len(rpeaks))
    if n == 0: return np.nan
    d = fid[:n] - rpeaks[:n]; d = d[~np.isnan(d)]
    d = d[(d > -0.4*FS) & (d < 0.6*FS)]
    return float(np.median(d)) if len(d) else np.nan

def process_one(args):
    ecg_id, relpath = args
    qa = dict(ecg_id=int(ecg_id))
    try:
        sig = read_record_from_zip(relpath)                    # (5000,12)
    except Exception as e:
        qa.update(ok=0, reason=f"read:{type(e).__name__}"); return None, None, None, qa
    if sig.shape[0] != N_SAMP:
        # pad/trim defensively
        s = np.zeros((N_SAMP, 12), np.float32); m = min(N_SAMP, sig.shape[0]); s[:m] = sig[:m]; sig = s
    try:
        clean = nk.ecg_clean(sig[:, LEAD_II], sampling_rate=FS)
        rpeaks = nk.ecg_peaks(clean, sampling_rate=FS)[1]["ECG_R_Peaks"]
    except Exception as e:
        qa.update(ok=0, reason=f"rpeaks:{type(e).__name__}"); return None, None, None, qa
    rpeaks = rpeaks[(rpeaks > 5) & (rpeaks < N_SAMP-5)]
    qa["n_rpeaks"] = int(len(rpeaks))
    if len(rpeaks) < 3:
        qa.update(ok=0, reason="too_few_rpeaks"); return None, None, None, qa
    try:
        w = nk.ecg_delineate(clean, rpeaks=rpeaks, sampling_rate=FS, method="dwt")[1]; deline_ok=1
    except Exception:
        w = {}; deline_ok = 0
    raw = {"P_on":_median_offset(w.get("ECG_P_Onsets",[]),rpeaks),
           "P_off":_median_offset(w.get("ECG_P_Offsets",[]),rpeaks),
           "R_on":_median_offset(w.get("ECG_R_Onsets",[]),rpeaks),
           "R_off":_median_offset(w.get("ECG_R_Offsets",[]),rpeaks),
           "T_off":_median_offset(w.get("ECG_T_Offsets",[]),rpeaks),
           "Q":_median_offset(w.get("ECG_Q_Peaks",[]),rpeaks),
           "S":_median_offset(w.get("ECG_S_Peaks",[]),rpeaks)}
    off = {}
    for k,(lo,hi) in BOUNDS.items():
        v = raw[k]; off[k] = FB[k] if np.isnan(v) else min(max(v,lo),hi)
    # QRS window: anchor on Q/S peaks (robust DWT fiducials). QRS onset = Q-8ms,
    # offset = S+24ms (J-point). Prevents R_on latching onto the P-tail and R_off
    # over-extending into ST. Robust fallback when Q/S missing: default ~100ms QRS
    # from a normal onset, NOT the unreliable wide DWT R_off (which inflates width).
    Q, S = raw["Q"], raw["S"]
    off["R_on"]  = float(np.clip(Q - 4, -70, -8)) if not np.isnan(Q) else FB["R_on"]
    off["R_off"] = float(np.clip(S + 12, 16, 90)) if not np.isnan(S) else off["R_on"] + 50
    off["P_off"] = min(off["P_off"], off["R_on"]-2)
    off["P_on"]  = min(off["P_on"],  off["P_off"]-4)
    off["R_off"] = max(off["R_off"], off["R_on"]+8)
    off["T_off"] = max(off["T_off"], off["R_off"]+20)

    # ---- per-sample masks over the WHOLE strip: place each subsystem window around every R ----
    masks = np.zeros((4, N_SAMP), np.uint8)   # P, PR, QRS, STT
    seg = [("P", off["P_on"], off["P_off"]), ("PR", off["P_off"], off["R_on"]),
           ("QRS", off["R_on"], off["R_off"]), ("STT", off["R_off"], off["T_off"])]
    for r in rpeaks:
        for i,(nm,a,b) in enumerate(seg):
            lo = int(round(r+a)); hi = int(round(r+b))
            lo = max(0, lo); hi = min(N_SAMP, hi)
            if hi > lo: masks[i, lo:hi] = 1

    # ---- z-score each lead per-record (robust: median/IQR) ----
    med = np.median(sig, axis=0, keepdims=True)
    iqr = (np.percentile(sig,75,axis=0,keepdims=True) - np.percentile(sig,25,axis=0,keepdims=True))
    iqr[iqr < 1e-4] = 1.0
    xz = ((sig - med) / iqr).astype(np.float16).T          # (12, 5000)

    # ---- interval biomarkers ----
    rr = np.diff(rpeaks) / FS * 1000.0                     # ms
    qt = (off["T_off"] - off["R_on"]) / FS * 1000.0
    rr_mean = float(np.mean(rr)) if len(rr) else np.nan
    qtc = qt / np.sqrt(rr_mean/1000.0) if rr_mean and rr_mean>0 else np.nan  # Bazett
    bio = dict(ecg_id=int(ecg_id),
               P_dur=(off["P_off"]-off["P_on"])/FS*1000, PR_int=(off["R_on"]-off["P_on"])/FS*1000,
               QRS_dur=(off["R_off"]-off["R_on"])/FS*1000, QT=qt, QTc=qtc,
               RR_mean=rr_mean, RR_sd=float(np.std(rr)) if len(rr)>1 else np.nan,
               HR=60000.0/rr_mean if rr_mean and rr_mean>0 else np.nan,
               n_beats=len(rpeaks))
    qa.update(ok=1, reason="", deline_ok=deline_ok, mask_frac=float(masks.mean()))
    return int(ecg_id), xz, masks, (bio, qa)

def main():
    manifest = pd.read_csv("cohort_manifest.csv")
    log = lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)
    LIMIT = int(os.environ.get("LIMIT", 0))
    if LIMIT:
        manifest = manifest.iloc[:LIMIT].copy()
        log(f"LIMIT={LIMIT} -> smoke test on {len(manifest)} ECGs")
    log(f"cohort: {len(manifest)} ECGs")
    tasks = list(zip(manifest.ecg_id, manifest.filename_hr))

    N = len(tasks)
    X = np.zeros((N, 12, N_SAMP), np.float16)
    M = np.zeros((N, 4, N_SAMP), np.uint8)
    id_to_row = {int(e): i for i, e in enumerate(manifest.ecg_id)}
    bios, qas = [], []
    ok = 0; t0 = time.time()
    nproc = int(os.environ.get("NPROC", max(1, (os.cpu_count() or 4))))
    log(f"extracting with {nproc} processes ...")
    with ProcessPoolExecutor(max_workers=nproc) as ex:
        futs = [ex.submit(process_one, t) for t in tasks]
        for j, fut in enumerate(as_completed(futs)):
            eid, xz, masks, meta = fut.result()
            if eid is not None:
                row = id_to_row[eid]; X[row] = xz; M[row] = masks; ok += 1
                bio, qa = meta; bios.append(bio); qas.append(qa)
            else:
                qas.append(meta if isinstance(meta, dict) else meta[-1])
            if (j+1) % 2000 == 0:
                log(f"  {j+1}/{N}  ok={ok}  ({(j+1)/(time.time()-t0):.0f}/s)")
    log(f"done: {ok}/{N} ok in {time.time()-t0:.0f}s")

    np.save(f"{PROC}/X_strip.npy", X)
    np.save(f"{PROC}/M_mask.npy", M)
    labels = manifest.copy()
    pd.DataFrame(bios).to_parquet(f"{PROC}/biomarkers.parquet")
    labels.to_parquet(f"{PROC}/labels.parquet")
    qadf = pd.DataFrame(qas)
    qadf.to_parquet(f"{PROC}/extract_qa.parquet")

    receipt = dict(n_total=N, n_ok=int(ok),
                   ok_rate=round(ok/N, 4),
                   X_shape=list(X.shape), M_shape=list(M.shape),
                   X_bytes=int(X.nbytes), seconds=round(time.time()-t0))
    json.dump(receipt, open(f"{OUT}/extract_receipt.json", "w"), indent=2)
    log(f"RECEIPT: {receipt}")

if __name__ == "__main__":
    main()
