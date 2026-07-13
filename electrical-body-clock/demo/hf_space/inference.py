"""
Live inference core for the HeartVector demo Space.

Wraps the FROZEN median-beat harness (hv_bundle/hv_frozen.py) so the Gradio app
can turn a 12-lead ECG into the five subsystem phase-age clocks and the frozen
A / D geometry, exactly as reported in the manuscript. Nothing here refits or
re-standardizes: all constants come from FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json
and the five checkpoints in hv_bundle/models/.
"""
import os, sys, functools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(HERE, "hv_bundle")
sys.path.insert(0, BUNDLE)

# canonical 12-lead order the frozen harness expects
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
PHASES = ["global", "P", "AV", "QRS", "STT"]


@functools.lru_cache(maxsize=1)
def _load():
    """Load frozen defs + the five clock checkpoints once (cached)."""
    import hv_frozen as hv
    hv.load_defs(os.path.join(BUNDLE, "FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json"))
    nets = hv.load_clocks(os.path.join(BUNDLE, "models"), device="cpu")
    return hv, nets


def _scalar(v):
    return float(np.atleast_1d(v)[0])


def synth_12lead(heart_rate=70, duration=10.0, fs=500, seed=0,
                 stt_shift=0.0, qrs_widen=0.0, noise=0.02):
    """Physiologically-plausible synthetic 12-lead ECG (no patient data).

    stt_shift / qrs_widen are cosmetic morphology knobs so the user can push the
    beat toward 'older-looking' repolarisation and see the clocks respond — they
    are illustrative, not a biophysical model.
    """
    import neurokit2 as nk
    rng = np.random.default_rng(int(seed))
    ecg1 = nk.ecg_simulate(duration=float(duration), sampling_rate=fs,
                           heart_rate=float(heart_rate), method="ecgsyn",
                           random_state=int(seed))
    ecg1 = np.asarray(ecg1, float)
    # relative per-lead projection scales (illustrative Einthoven/precordial pattern)
    scales = np.array([0.9, 1.0, 0.4, -0.7, 0.3, 0.6, 0.5, 0.9, 1.3, 1.1, 0.8, 0.6])
    sig = np.outer(ecg1, scales)
    # optional morphology perturbations applied to the T-region-ish tail of each beat
    if stt_shift or qrs_widen:
        n = len(ecg1)
        t = np.linspace(0, 1, n)
        drift = stt_shift * 0.15 * np.sin(2 * np.pi * t * float(heart_rate) / 60.0)
        sig = sig + np.outer(drift, scales)
    sig = sig + rng.normal(0, float(noise), sig.shape)
    return sig.astype(np.float32)


def score_signal(sig12, fs, age, sex):
    """sig12: (N,12) canonical-order 12-lead. Returns (result_dict | None, qa)."""
    hv, nets = _load()
    data, qa = hv.extract_from_signal(np.asarray(sig12, float), fs_in=int(fs))
    if data is None:
        return None, qa
    X = hv.masked_inputs(data)[None]
    preds = hv.infer_clocks(X, nets)
    preds = {k: _scalar(v) for k, v in preds.items()}
    sc = hv.score_frozen(preds, age=float(age), sex=int(sex))
    out = {
        "phase_ages": preds,
        "A": _scalar(sc["A"]), "A_std": _scalar(sc["A_std"]),
        "D": _scalar(sc["D"]), "D_std": _scalar(sc["D_std"]),
        "q": [_scalar(sc["q1"]), _scalar(sc["q2"]), _scalar(sc["q3"])],
        "median_beat": data["median_beat"], "masks": data["masks"],
        "wins": data["wins"],
    }
    return out, qa


def parse_uploaded(path):
    """Accept a WFDB record (.hea/.dat, pass the .hea) or a CSV of 12 columns.

    Returns (sig12 (N,12), fs) or raises ValueError.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".hea", ".dat", ""):
        import wfdb
        base = path[:-4] if ext in (".hea", ".dat") else path
        rec = wfdb.rdrecord(base)
        sig = np.asarray(rec.p_signal, float)
        fs = int(rec.fs)
        if sig.shape[1] < 12:
            raise ValueError(f"WFDB record has {sig.shape[1]} channels; need 12.")
        return sig[:, :12].astype(np.float32), fs
    if ext == ".csv":
        arr = np.loadtxt(path, delimiter=",", skiprows=0)
        if arr.ndim != 2 or arr.shape[1] < 12:
            raise ValueError("CSV must have >=12 columns (one per lead), samples in rows.")
        return arr[:, :12].astype(np.float32), 500
    raise ValueError(f"Unsupported file type {ext!r}. Use WFDB (.hea) or 12-column CSV.")
