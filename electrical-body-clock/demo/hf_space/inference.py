"""
Live inference core for the HeartVector demo Space.

Wraps the FROZEN median-beat harness (hv_bundle/hv_frozen.py) so the Gradio app
can turn a 12-lead ECG into the five subsystem phase-age clocks and the frozen
A / D geometry, exactly as reported in the manuscript. Nothing here refits or
re-standardizes: all constants come from FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json
and the five checkpoints in hv_bundle/models/.
"""
import os, sys, functools
import math
import re
import shutil
import tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(HERE, "hv_bundle")
sys.path.insert(0, BUNDLE)

# canonical 12-lead order the frozen harness expects
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
PHASES = ["global", "P", "AV", "QRS", "STT"]

# Upload limits are deliberately conservative. The frozen models consume a
# single short 12-lead recording, not Holter data or arbitrary clinical files.
MAX_HEADER_BYTES = 64 * 1024
MAX_SIGNAL_FILE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_UPLOAD_BYTES = 26 * 1024 * 1024
MAX_DURATION_SECONDS = 300
SAFE_UPLOAD_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


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


def _file_path_and_name(item):
    """Return a Gradio/local upload's filesystem path and original basename."""
    if isinstance(item, dict):
        path = item.get("path") or item.get("name")
        original = item.get("orig_name") or item.get("original_name")
    elif isinstance(item, (str, os.PathLike)):
        path, original = os.fspath(item), None
    else:
        path = getattr(item, "path", None) or getattr(item, "name", None)
        original = getattr(item, "orig_name", None) or getattr(item, "original_name", None)
    if not path:
        raise ValueError("The upload did not provide a readable local file path.")
    path = os.fspath(path)
    if not os.path.isfile(path) or os.path.islink(path):
        raise ValueError("Every selected upload must be a regular file.")
    if original:
        original = os.fspath(original)
        if "/" in original or "\\" in original:
            raise ValueError("Uploaded filenames may not contain directory paths.")
        name = original
    else:
        name = os.path.basename(path)
    if not SAFE_UPLOAD_NAME.fullmatch(name):
        raise ValueError(
            "Use a simple filename containing only letters, numbers, dot, dash, or underscore "
            "(maximum 128 characters).")
    return path, name


def _normalize_uploads(files):
    if files is None:
        return []
    if isinstance(files, (str, os.PathLike, dict)) or not isinstance(files, (list, tuple)):
        files = [files]
    items = [_file_path_and_name(item) for item in files]
    real_paths = [os.path.realpath(path) for path, _ in items]
    if len(set(real_paths)) != len(real_paths):
        raise ValueError("The same file was selected more than once.")
    return items


def _check_file_sizes(items):
    total = 0
    for path, name in items:
        size = os.path.getsize(path)
        ext = os.path.splitext(name)[1].lower()
        limit = MAX_HEADER_BYTES if ext == ".hea" else MAX_SIGNAL_FILE_BYTES
        if size <= 0:
            raise ValueError(f"{name} is empty.")
        if size > limit:
            raise ValueError(
                f"{name} is too large ({size / 1024 / 1024:.1f} MiB); "
                f"the limit for this file type is {limit / 1024 / 1024:.1f} MiB.")
        total += size
    if total > MAX_TOTAL_UPLOAD_BYTES:
        raise ValueError(
            f"The selected files total {total / 1024 / 1024:.1f} MiB; "
            f"the combined limit is {MAX_TOTAL_UPLOAD_BYTES / 1024 / 1024:.1f} MiB.")


def _parse_wfdb_header(header_path, header_name, dat_name):
    """Validate the bounded WFDB header before wfdb reads the signal payload."""
    try:
        with open(header_path, "rb") as handle:
            raw = handle.read(MAX_HEADER_BYTES + 1)
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError("The WFDB header must be a small UTF-8/ASCII text file.") from exc
    if "\x00" in text:
        raise ValueError("The WFDB header contains binary data.")
    lines = [line.strip() for line in text.splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError("The WFDB header is empty.")
    first = lines[0].split()
    if len(first) < 4:
        raise ValueError("The WFDB header's first line must include record, leads, rate, and samples.")
    record_name, n_sig_token, fs_token, n_samples_token = first[:4]
    if "/" in record_name or "\\" in record_name or record_name != os.path.splitext(header_name)[0]:
        raise ValueError("The WFDB record name must match the .hea/.dat filename stem.")
    try:
        n_sig = int(n_sig_token)
        fs = int(round(float(fs_token.split("/")[0])))
        n_samples = int(n_samples_token)
    except (TypeError, ValueError) as exc:
        raise ValueError("The WFDB header has invalid lead, sampling-rate, or sample-count metadata.") from exc
    if n_sig != 12:
        raise ValueError(f"WFDB record declares {n_sig} channels; exactly 12 standard leads are required.")
    _validate_sample_count(n_samples, fs)
    if len(lines) < 1 + n_sig:
        raise ValueError("The WFDB header has fewer signal lines than its declared lead count.")
    data_refs = []
    for line in lines[1:1 + n_sig]:
        ref = line.split()[0]
        if "/" in ref or "\\" in ref or os.path.basename(ref) != ref:
            raise ValueError("WFDB signal references must be local filenames, not paths.")
        data_refs.append(ref)
    if set(data_refs) != {dat_name}:
        raise ValueError(
            "The WFDB header must reference only the selected matching .dat file on every lead.")
    return fs, n_samples


def _validate_sample_count(n_samples, fs):
    if fs < 100 or fs > 2000:
        raise ValueError(f"Sampling rate {fs} Hz is outside the supported 100-2000 Hz range.")
    minimum = int(math.ceil(2.0 * fs))
    maximum = int(MAX_DURATION_SECONDS * fs)
    if n_samples < minimum:
        raise ValueError(
            f"Record has {n_samples} samples at {fs} Hz; at least 2 seconds are required.")
    if n_samples > maximum:
        raise ValueError(
            f"Record has {n_samples} samples ({n_samples / fs:.1f}s); "
            f"the upload limit is {MAX_DURATION_SECONDS} seconds.")


def _validate_csv_structure(path, fs):
    """Count rows/columns with bounded memory before NumPy parses numeric values."""
    fs = int(fs)
    if fs < 100 or fs > 2000:
        raise ValueError(f"Sampling rate {fs} Hz is outside the supported 100-2000 Hz range.")
    max_rows = int(MAX_DURATION_SECONDS * fs)
    rows = 0
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            for line_no, line in enumerate(handle, start=1):
                if len(line) > 8192:
                    raise ValueError(f"CSV row {line_no} is unreasonably long.")
                stripped = line.strip()
                if not stripped:
                    raise ValueError(f"CSV row {line_no} is blank; provide a dense numeric matrix.")
                column_count = len(stripped.split(","))
                if column_count != 12:
                    raise ValueError(
                        f"CSV row {line_no} has {column_count} columns; exactly 12 are required.")
                rows += 1
                if rows > max_rows:
                    raise ValueError(
                        f"CSV exceeds the {MAX_DURATION_SECONDS}-second limit at {fs} Hz.")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV input must be UTF-8 text containing numeric samples only.") from exc
    _validate_sample_count(rows, fs)
    return rows


def parse_uploaded_files(files, csv_fs=500):
    """Safely accept exactly one CSV or one matching WFDB .hea/.dat pair.

    Selected uploads are size- and structure-checked before numeric/signal
    parsing. WFDB files are copied into a short-lived private directory so only
    the validated pair can be resolved by the WFDB reader; that copy is removed
    immediately after parsing.
    """
    items = _normalize_uploads(files)
    if not items:
        raise ValueError("Select exactly one CSV or one matching .hea + .dat pair.")
    if len(items) not in (1, 2):
        raise ValueError("Select exactly one CSV or exactly two matching WFDB files (.hea + .dat).")
    _check_file_sizes(items)
    extensions = [os.path.splitext(name)[1].lower() for _, name in items]
    if len(items) == 1:
        path, name = items[0]
        if extensions != [".csv"]:
            raise ValueError("A single upload must be a 12-column .csv file.")
        _validate_csv_structure(path, int(csv_fs))
        return _parse_validated_path(path, csv_fs=int(csv_fs))

    if sorted(extensions) != [".dat", ".hea"]:
        raise ValueError("Two-file uploads must contain exactly one .hea and one .dat file.")
    by_ext = {os.path.splitext(name)[1].lower(): (path, name) for path, name in items}
    hea_path, hea_name = by_ext[".hea"]
    dat_path, dat_name = by_ext[".dat"]
    if os.path.splitext(hea_name)[0] != os.path.splitext(dat_name)[0]:
        raise ValueError("WFDB .hea and .dat filenames must have the same stem.")
    _parse_wfdb_header(hea_path, hea_name, dat_name)
    with tempfile.TemporaryDirectory(prefix="heartvector_upload_") as tmp:
        staged_hea = os.path.join(tmp, hea_name)
        staged_dat = os.path.join(tmp, dat_name)
        shutil.copyfile(hea_path, staged_hea)
        shutil.copyfile(dat_path, staged_dat)
        return _parse_validated_path(staged_hea, csv_fs=int(csv_fs))


def parse_uploaded(path, csv_fs=500):
    """Backward-compatible local-file wrapper around :func:`parse_uploaded_files`.

    A WFDB path automatically includes its same-stem sibling; a CSV is passed as
    the single permitted upload.
    """
    ext = os.path.splitext(os.fspath(path))[1].lower()
    if ext == ".csv":
        return parse_uploaded_files([path], csv_fs=csv_fs)
    if ext in (".hea", ".dat", ""):
        base = os.fspath(path)[:-4] if ext in (".hea", ".dat") else os.fspath(path)
        return parse_uploaded_files([base + ".hea", base + ".dat"], csv_fs=csv_fs)
    raise ValueError(f"Unsupported file type {ext!r}. Use WFDB (.hea + .dat) or a 12-column CSV.")


def _parse_validated_path(path, csv_fs=500):
    """Parse a file only after the public upload validator has accepted it.

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
        if arr.ndim != 2 or arr.shape[1] != 12:
            raise ValueError(
                "CSV must have exactly 12 columns (one per lead in canonical order "
                "I, II, III, aVR, aVL, aVF, V1-V6), samples in rows.")
        if arr.shape[0] < arr.shape[1]:
            raise ValueError(
                f"CSV looks transposed ({arr.shape[0]} rows x {arr.shape[1]} cols): "
                "samples should be in rows, leads in columns.")
        sig = arr.astype(float)
        fs = int(csv_fs)
        _validate_signal(sig, fs)
        return sig.astype(np.float32), fs
    raise ValueError(f"Unsupported file type {ext!r}. Use WFDB (.hea + .dat) or a 12-column CSV.")


def _validate_signal(sig, fs):
    """Sanity-check duration, sampling rate, and amplitude units (expect mV)."""
    sig = np.asarray(sig)
    if sig.ndim != 2 or sig.shape[1] != 12:
        raise ValueError(f"Signal shape must be samples x 12 leads; received {sig.shape}.")
    if not np.isfinite(sig).all():
        raise ValueError("Signal contains NaN or infinite values.")
    if fs < 100 or fs > 2000:
        raise ValueError(f"Sampling rate {fs} Hz is outside the supported 100-2000 Hz range.")
    dur = sig.shape[0] / float(fs)
    if dur < 2.0:
        raise ValueError(f"Record is only {dur:.1f}s; need at least ~2s of signal.")
    if dur > MAX_DURATION_SECONDS:
        raise ValueError(
            f"Record is {dur:.1f}s; the upload limit is {MAX_DURATION_SECONDS} seconds.")
    # PTB-XL-style ECGs are in mV, typically |amp| < ~10 mV. Flag likely-microvolt input.
    p99 = float(np.nanpercentile(np.abs(sig), 99))
    if p99 > 50:
        raise ValueError(
            f"Amplitudes look too large (99th pct |x| = {p99:.0f}); "
            "signal should be in millivolts (mV), not microvolts. Divide by 1000 if needed.")
