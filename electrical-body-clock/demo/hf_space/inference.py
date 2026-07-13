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
                 stt_shift=0.0, noise=0.02):
    """Synthetic 12-lead ECG for INTERFACE ILLUSTRATION ONLY (no patient data).

    This is a rendering aid so the controls and plots can be exercised without an
    uploaded record. It is NOT a biophysical heart model and any age it produces
    is an artefact of the interface, not a biological measurement. Use the
    bundled real PTB-XL examples or upload a real record for meaningful output.

    Leads are built from per-lead beat templates (distinct P/QRS/T morphology per
    lead), NOT scaled copies of one waveform. `stt_shift` perturbs ONLY the
    ST-T segment (J-point to end of T) of each beat, leaving P and QRS untouched.
    """
    import neurokit2 as nk
    rng = np.random.default_rng(int(seed))
    fs = int(fs)
    n = int(float(duration) * fs)
    # one delineated reference beat -> locate ST-T region, then build per-lead templates
    ref = np.asarray(nk.ecg_simulate(duration=float(duration), sampling_rate=fs,
                                     heart_rate=float(heart_rate), method="ecgsyn",
                                     random_state=int(seed)), float)[:n]
    # per-lead relative amplitudes AND small morphology variation so leads are not
    # identical scaled copies (distinct QRS/T balance per lead, illustrative only)
    qrs_scale = np.array([0.9, 1.0, 0.4, -0.7, 0.3, 0.6, -0.5, -0.2, 0.4, 0.9, 1.1, 0.8])
    t_scale   = np.array([0.25, 0.35, 0.10, -0.20, 0.10, 0.20, 0.15, 0.30, 0.35, 0.30, 0.25, 0.20])
    # split reference into a QRS-ish fast component and a T-ish slow component by
    # band-splitting around the beat, so per-lead QRS and T amplitudes differ
    from scipy.signal import butter, filtfilt
    bh, ah = butter(2, 8.0 / (fs / 2), "high")
    bl, al = butter(2, 6.0 / (fs / 2), "low")
    qrs_comp = filtfilt(bh, ah, ref)     # fast deflections (QRS, P)
    t_comp = filtfilt(bl, al, ref)       # slow deflections (T wave, baseline)
    sig = (np.outer(qrs_comp, qrs_scale) + np.outer(t_comp, t_scale)).astype(float)

    # ST-T-LOCAL perturbation: build a per-sample ST-T mask from the reference
    # beat's R peaks (J-point ~60 ms after R, T end ~ next-beat onset) and apply
    # the shift ONLY inside that window.
    if stt_shift:
        try:
            _, info = nk.ecg_peaks(ref, sampling_rate=fs)
            rpeaks = np.asarray(info["ECG_R_Peaks"], int)
        except Exception:
            rpeaks = np.arange(0, n, max(1, int(fs * 60.0 / float(heart_rate))))
        stt_mask = np.zeros(n, float)
        j_off = int(0.06 * fs)           # J-point ~60 ms after R
        t_end = int(0.42 * fs)           # end of T ~420 ms after R
        for r in rpeaks:
            a, b = r + j_off, min(n, r + t_end)
            if a < b:
                stt_mask[a:b] = np.hanning(b - a)  # smooth localized bump
        # elevate/depress the ST-T slow component only, per-lead
        sig = sig + float(stt_shift) * 0.20 * np.outer(stt_mask, t_scale)

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


def _canonical_name(nm):
    """Normalize a lead name to canonical form (case/whitespace/aVR variants)."""
    s = str(nm).strip().upper().replace(" ", "")
    alias = {"AVR": "aVR", "AVL": "aVL", "AVF": "aVF",
             "AVR ": "aVR", "1": "I", "2": "II", "3": "III"}
    if s in ("I", "II", "III"):
        return s
    if s in alias:
        return alias[s]
    # V1..V6 pass through; otherwise title-case
    if s.startswith("V") and s[1:].isdigit():
        return s
    return alias.get(s, nm if nm in LEADS else s)


def _reorder_to_canonical(sig, names):
    """Reorder columns of sig (N,C) to canonical LEADS order using channel names.

    Raises ValueError if the 12 canonical leads cannot all be matched.
    """
    canon = {}
    for j, nm in enumerate(names):
        c = _canonical_name(nm)
        if c in LEADS and c not in canon:
            canon[c] = j
    missing = [l for l in LEADS if l not in canon]
    if missing:
        raise ValueError(
            "Uploaded record is missing canonical leads "
            f"{missing}. Found channels: {list(names)}. "
            "Provide all 12 standard leads (I, II, III, aVR, aVL, aVF, V1-V6).")
    idx = [canon[l] for l in LEADS]
    return sig[:, idx]


def parse_uploaded(path, csv_fs=500):
    """Accept a WFDB record (needs BOTH .hea and .dat) or a 12-column CSV.

    - WFDB: leads are reordered to canonical order using the header `sig_name`;
      units are converted to mV using the header if needed.
    - CSV: the sampling rate must be supplied (`csv_fs`, default 500 Hz) because a
      bare CSV carries no header; columns are assumed to be leads in canonical
      order (I, II, III, aVR, aVL, aVF, V1-V6), samples in rows, amplitude in mV.

    Returns (sig12 (N,12) canonical order in mV, fs). Raises ValueError with an
    actionable message on any validation failure.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".hea", ".dat", ""):
        import wfdb
        base = path[:-4] if ext in (".hea", ".dat") else path
        if not (os.path.exists(base + ".hea") and os.path.exists(base + ".dat")):
            raise ValueError(
                "WFDB upload needs BOTH the .hea header and the .dat signal file. "
                "Upload them together (or zip the pair).")
        rec = wfdb.rdrecord(base)
        sig = np.asarray(rec.p_signal, float)   # wfdb returns physical units (mV for PTB-XL)
        fs = int(rec.fs)
        names = list(rec.sig_name) if rec.sig_name else []
        if sig.shape[1] < 12:
            raise ValueError(f"WFDB record has {sig.shape[1]} channels; need all 12 leads.")
        if len(names) >= 12:
            sig = _reorder_to_canonical(sig, names)
        else:
            sig = sig[:, :12]   # no names: assume already canonical
        _validate_signal(sig, fs)
        return sig.astype(np.float32), fs
    if ext == ".csv":
        arr = np.loadtxt(path, delimiter=",")
        if arr.ndim != 2 or arr.shape[1] < 12:
            raise ValueError(
                "CSV must have >=12 columns (one per lead in canonical order "
                "I, II, III, aVR, aVL, aVF, V1-V6), samples in rows.")
        if arr.shape[0] < arr.shape[1]:
            raise ValueError(
                f"CSV looks transposed ({arr.shape[0]} rows x {arr.shape[1]} cols): "
                "samples should be in rows, leads in columns.")
        sig = arr[:, :12].astype(float)
        fs = int(csv_fs)
        _validate_signal(sig, fs)
        return sig.astype(np.float32), fs
    raise ValueError(f"Unsupported file type {ext!r}. Use WFDB (.hea + .dat) or a 12-column CSV.")


def _validate_signal(sig, fs):
    """Sanity-check duration, sampling rate, and amplitude units (expect mV)."""
    if fs < 100 or fs > 2000:
        raise ValueError(f"Sampling rate {fs} Hz is outside the supported 100-2000 Hz range.")
    dur = sig.shape[0] / float(fs)
    if dur < 2.0:
        raise ValueError(f"Record is only {dur:.1f}s; need at least ~2s of signal.")
    # PTB-XL-style ECGs are in mV, typically |amp| < ~10 mV. Flag likely-microvolt input.
    p99 = float(np.nanpercentile(np.abs(sig), 99))
    if p99 > 50:
        raise ValueError(
            f"Amplitudes look too large (99th pct |x| = {p99:.0f}); "
            "signal should be in millivolts (mV), not microvolts. Divide by 1000 if needed.")
