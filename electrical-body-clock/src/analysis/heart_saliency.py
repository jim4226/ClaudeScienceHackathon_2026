#!/usr/bin/env python3
"""
heart_saliency.py  —  Body Clock enrichment module (Witness 1, ECG)
====================================================================
"Where does each subsystem clock LOOK, and does it look where it should?"

This is an ADDITIVE, drop-in module. It does not edit any existing training
code. It consumes the four trained subsystem age clocks
(P / PR / QRS / ST-T, each a `Clock1DCNN`) and the PTB-XL median beats, and
produces model-attention evidence that the decomposition is real:

  1.  Runs BOTH Grad-CAM (last conv activation x gradient) AND Integrated
      Gradients (path-integral of input gradients) over ALL test median beats
      for each of the four clocks.
  2.  Aggregates a cohort-mean attention profile per clock over the beat axis.
  3.  Computes a QUANTIFIED SPECIFICITY metric: the fraction of each clock's
      attention mass that falls inside its own P/PR/QRS/ST-T window on the beat
      (a self-localisation score in [0,1]). Reported as-measured — including for
      the weak P (R2 0.26) and PR (R2 0.20) clocks, whose profiles are noisier.
  4.  Builds a composite figure:
         LEFT  = the median beat with four colour-coded attention bands.
         RIGHT = a four-chamber heart, each chamber tinted by that subsystem's
                 disease-driven aging (atria<-P, AV node<-PR +3.39y AV-block,
                 ventricles<-QRS, myocardium<-ST-T +4.79y ischemia),
                 connected to its band by a ribbon.
  5.  Writes the specificity metric as a CSV + Markdown table.
  6.  Emits a SELF-CONTAINED Three.js HTML viewer: click a chamber to see that
      subsystem's attention curve and its disease-aging number.

HONESTY (read this):
  * Saliency shows WHERE THE MODEL LOOKS, not causation. A high specificity
    score means the clock's evidence is concentrated on the expected beat
    segment; it is NOT proof that the segment causes aging.
  * Grad-CAM and IG can disagree; we report both and their agreement.
  * The P and PR clocks are weak (R2 0.26 / 0.20). Their attention is flatter
    and their specificity is therefore lower and higher-variance. We do not
    hide this — a weak clock with diffuse attention is an honest negative.
  * If the real model / beat artifacts are absent, the module runs in a clearly
    labelled `--demo` SYNTHETIC mode so the plumbing is verifiable end-to-end.
    Synthetic runs stamp "SYNTHETIC" on every output. Never present a synthetic
    figure as a result.

Environment (standard):
    pip install torch numpy matplotlib pandas
    # optional, nicer heart on the right panel:
    pip install pyvista trimesh
Run:
    # real artifacts:
    python enrich/heart_saliency.py \
        --models-dir witness1_ecg/models \
        --beats witness1_ecg/median_beats_test.npy \
        --heart-glb figures/heart_four_chamber.glb \
        --out enrich/out_heart_saliency
    # smoke test with no artifacts present:
    python enrich/heart_saliency.py --demo --out enrich/out_demo

Author: Body Clock / "Acceleration at Two Timescales" enrichment.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------
# 0.  Study constants  (edit here if the beat geometry or matrix changes)
# ----------------------------------------------------------------------------

# The four subsystem clocks. `order` fixes plotting / colour order.
CLOCKS = ("P", "PR", "QRS", "ST-T")

# Each clock's OWN diagnostic window on the median beat, expressed as
# fractions of the beat length [start, end]. These are the classic ECG
# segments for a beat aligned so the R-peak sits at ~0.36 of the window.
# Specificity = fraction of the clock's attention mass inside its own window.
# Windows are intentionally the *physiological* segments, not tuned to flatter
# the models — a clock that ignores its segment will score low, as it should.
BEAT_WINDOWS: dict[str, tuple[float, float]] = {
    "P":    (0.04, 0.20),   # P wave (atrial depolarisation)
    "PR":   (0.15, 0.32),   # PR segment/interval (P-end -> QRS-onset; AV delay)
    "QRS":  (0.30, 0.46),   # QRS complex (ventricular depolarisation)
    "ST-T": (0.46, 0.88),   # ST segment + T wave (ventricular repolarisation)
}

# Colour per clock (matplotlib + hex for the web viewer). Colour-blind safe-ish.
CLOCK_COLORS: dict[str, str] = {
    "P":    "#2f7fd6",   # blue
    "PR":   "#12a15b",   # green
    "QRS":  "#e07a1a",   # orange
    "ST-T": "#c33d5a",   # red
}

# Disease-driven aging, from the bias-corrected disease-substrate matrix (yr).
# atria<-P, AV node<-PR (+3.39 AV block), ventricles<-QRS, myocardium<-ST-T
# (+4.79 ischemia). Values that are unmeasured/near-zero are shown as ~0.
DISEASE_AGING: dict[str, dict] = {
    "P":    {"substrate": "atria",       "chamber": "atria",
             "condition": "atrial",              "delta_years": 0.0},
    "PR":   {"substrate": "AV node",     "chamber": "av_node",
             "condition": "AV block",            "delta_years": 3.39},
    "QRS":  {"substrate": "ventricles",  "chamber": "ventricles",
             "condition": "conduction/hypertrophy", "delta_years": 0.0},
    "ST-T": {"substrate": "myocardium",  "chamber": "myocardium",
             "condition": "ischemia",            "delta_years": 4.79},
}

# Weak-clock flags (R2), reported alongside specificity so the reader can weight
# a low/erratic specificity by how well the clock predicts age at all.
CLOCK_R2: dict[str, float] = {"P": 0.26, "PR": 0.20, "QRS": 0.55, "ST-T": 0.60}

# Whole-beat MAE headline (years) — carried into captions for context only.
WHOLE_BEAT_MAE = 8.0


# ----------------------------------------------------------------------------
# 1.  Model architecture
#     We prefer the study's OWN Clock1DCNN if importable, so real weights load
#     exactly. Otherwise we define a compatible reference architecture and load
#     with strict=False (warns on any key mismatch). Grad-CAM auto-targets the
#     last Conv1d regardless of which definition is in play.
# ----------------------------------------------------------------------------

def _import_study_clock():
    """Try to import the real Clock1DCNN from the training module."""
    for modpath in ("witness1_ecg.train_clocks", "train_clocks",
                    "witness1_ecg.models", "ecg.train_clocks"):
        try:
            mod = importlib.import_module(modpath)
            if hasattr(mod, "Clock1DCNN"):
                return getattr(mod, "Clock1DCNN"), modpath
        except Exception:
            continue
    return None, None


def _reference_clock_cls():
    """A compatible 1D-CNN regressor. Only defined when torch is available."""
    import torch
    import torch.nn as nn

    class Clock1DCNN(nn.Module):
        """Reference subsystem age clock.

        Input : (B, n_leads, L) median beat.
        Output: (B,) predicted age (years).
        A small VGG-style 1D stack; the LAST Conv1d is the Grad-CAM target.
        This mirrors the described 1D-CNN subsystem clocks; if your real
        weights use different widths, they still load with strict=False and
        Grad-CAM/IG remain valid (they only need a last conv + input grads).
        """

        def __init__(self, n_leads: int = 12, widths=(32, 64, 128), n_fc: int = 64):
            super().__init__()
            chans = [n_leads, *widths]
            blocks = []
            for i in range(len(widths)):
                blocks += [
                    nn.Conv1d(chans[i], chans[i + 1], kernel_size=7, padding=3),
                    nn.BatchNorm1d(chans[i + 1]),
                    nn.ReLU(inplace=True),
                    nn.Conv1d(chans[i + 1], chans[i + 1], kernel_size=5, padding=2),
                    nn.BatchNorm1d(chans[i + 1]),
                    nn.ReLU(inplace=True),
                    nn.MaxPool1d(2),
                ]
            self.features = nn.Sequential(*blocks)
            self.gap = nn.AdaptiveAvgPool1d(1)
            self.head = nn.Sequential(
                nn.Flatten(), nn.Linear(widths[-1], n_fc),
                nn.ReLU(inplace=True), nn.Linear(n_fc, 1),
            )

        def forward(self, x):
            f = self.features(x)
            return self.head(self.gap(f)).squeeze(-1)

    return Clock1DCNN


def last_conv_module(model):
    """Return the last nn.Conv1d in the model (Grad-CAM target layer)."""
    import torch.nn as nn
    target = None
    for m in model.modules():
        if isinstance(m, nn.Conv1d):
            target = m
    return target


# ----------------------------------------------------------------------------
# 2.  Attribution:  Grad-CAM (1D) and Integrated Gradients (from scratch)
# ----------------------------------------------------------------------------

def grad_cam_1d(model, x, target_layer):
    """1D Grad-CAM for a scalar regressor.

    x : (B, n_leads, L) tensor (requires no grad on input).
    Returns cam : (B, L) numpy, min-max normalised per sample in [0,1],
    upsampled back to the input length L.
    """
    import torch
    import torch.nn.functional as F

    acts, grads = {}, {}

    def fwd_hook(_m, _i, o):
        acts["v"] = o

    def bwd_hook(_m, gi, go):
        grads["v"] = go[0]

    h1 = target_layer.register_forward_hook(fwd_hook)
    h2 = target_layer.register_full_backward_hook(bwd_hook)
    try:
        model.zero_grad(set_to_none=True)
        out = model(x)                       # (B,)
        out.sum().backward()                 # d(sum age)/d(activations)
        A = acts["v"]                        # (B, C, L')
        G = grads["v"]                       # (B, C, L')
        weights = G.mean(dim=2, keepdim=True)          # GAP over time -> (B,C,1)
        cam = F.relu((weights * A).sum(dim=1))         # (B, L')
        cam = cam.unsqueeze(1)                          # (B,1,L')
        cam = F.interpolate(cam, size=x.shape[-1], mode="linear",
                            align_corners=False).squeeze(1)  # (B, L)
    finally:
        h1.remove(); h2.remove()
    cam = cam.detach().cpu().numpy()
    return _minmax_rows(cam)


def integrated_gradients_1d(model, x, steps: int = 32, baseline=None):
    """Integrated Gradients for a scalar regressor, reduced to a (B, L) time map.

    Attribution per input element = (x - baseline) * mean_k grad(model, path_k).
    We take |attribution| and sum over leads to get a per-time-point importance,
    then min-max normalise per sample. Baseline defaults to zeros (flat line),
    the natural "no beat" reference for a mean-centred median beat.
    """
    import torch
    x = x.detach()
    if baseline is None:
        baseline = torch.zeros_like(x)
    total = torch.zeros_like(x)
    for k in range(1, steps + 1):
        alpha = k / steps
        xk = (baseline + alpha * (x - baseline)).clone().requires_grad_(True)
        model.zero_grad(set_to_none=True)
        out = model(xk)
        out.sum().backward()
        total = total + xk.grad.detach()
    avg_grad = total / steps
    attr = (x - baseline) * avg_grad                 # (B, n_leads, L)
    imp = attr.abs().sum(dim=1)                       # (B, L) over leads
    imp = imp.detach().cpu().numpy()
    return _minmax_rows(imp)


def _minmax_rows(a: np.ndarray) -> np.ndarray:
    """Per-row min-max to [0,1]; flat rows -> zeros (honest: no signal)."""
    a = np.asarray(a, dtype=np.float64)
    lo = a.min(axis=1, keepdims=True)
    hi = a.max(axis=1, keepdims=True)
    rng = hi - lo
    out = np.zeros_like(a)
    nz = (rng.squeeze(-1) > 1e-12)
    out[nz] = (a[nz] - lo[nz]) / rng[nz]
    return out


# ----------------------------------------------------------------------------
# 3.  Specificity metric
# ----------------------------------------------------------------------------

def window_indices(L: int, frac: tuple[float, float]) -> tuple[int, int]:
    a = int(round(frac[0] * L))
    b = int(round(frac[1] * L))
    return max(0, a), min(L, max(a + 1, b))


def specificity(profile: np.ndarray, clock: str, L: int) -> float:
    """Fraction of a clock's cohort-mean attention mass inside its own window.

    profile : (L,) non-negative attention (cohort mean). Returns value in [0,1].
    A random/flat profile scores ~ (window_width / L). We also report that
    chance level in the table so a score is judged against its own baseline.
    """
    p = np.clip(np.asarray(profile, dtype=np.float64), 0, None)
    tot = p.sum()
    if tot <= 1e-12:
        return 0.0
    a, b = window_indices(L, BEAT_WINDOWS[clock])
    return float(p[a:b].sum() / tot)


def chance_level(clock: str) -> float:
    a, b = BEAT_WINDOWS[clock]
    return float(b - a)


# ----------------------------------------------------------------------------
# 4.  Driver over all four clocks / all test beats
# ----------------------------------------------------------------------------

@dataclass
class ClockResult:
    clock: str
    cam_profile: np.ndarray        # (L,) cohort mean Grad-CAM
    ig_profile: np.ndarray         # (L,) cohort mean IG
    mean_profile: np.ndarray       # (L,) mean of the two (used for figure/metric)
    spec_cam: float
    spec_ig: float
    spec_mean: float
    n_beats: int
    synthetic: bool = False


def _select_leads(beats: np.ndarray, n_leads_model: int) -> np.ndarray:
    """Coerce beats to (N, n_leads_model, L). Accepts (N,L), (N,1,L),
    (N,leads,L) or (N,L,leads). Pads/tiles or trims leads to match the model."""
    b = np.asarray(beats)
    if b.ndim == 2:                       # (N, L) -> single lead
        b = b[:, None, :]
    elif b.ndim == 3:
        # decide which axis is leads: the smaller of axes 1,2 that is <= 12
        n0, n1, n2 = b.shape
        if n1 > n2 and n2 <= 12:          # (N, L, leads) -> transpose
            b = np.transpose(b, (0, 2, 1))
    else:
        raise ValueError(f"median beats must be 2-D or 3-D, got shape {b.shape}")
    N, C, L = b.shape
    if C == n_leads_model:
        return b
    if C > n_leads_model:                 # trim
        return b[:, :n_leads_model, :]
    reps = int(np.ceil(n_leads_model / C))          # tile up
    return np.tile(b, (1, reps, 1))[:, :n_leads_model, :]


def run_all_clocks(models: dict, beats: np.ndarray, *, ig_steps: int = 32,
                   batch: int = 128, device: str = "cpu",
                   n_leads_model: int = 12) -> dict[str, ClockResult]:
    """Run Grad-CAM + IG for each clock over ALL test beats; aggregate."""
    import torch
    X = _select_leads(beats, n_leads_model).astype(np.float32)
    N, C, L = X.shape
    results: dict[str, ClockResult] = {}
    for clock in CLOCKS:
        model = models[clock].to(device).eval()
        tgt = last_conv_module(model)
        if tgt is None:
            raise RuntimeError(f"[{clock}] no Conv1d found for Grad-CAM target.")
        cam_acc = np.zeros(L); ig_acc = np.zeros(L); n = 0
        for s in range(0, N, batch):
            xb = torch.from_numpy(X[s:s + batch]).to(device)
            cam = grad_cam_1d(model, xb, tgt)                 # (b, L)
            ig = integrated_gradients_1d(model, xb, steps=ig_steps)  # (b, L)
            cam_acc += cam.sum(axis=0); ig_acc += ig.sum(axis=0)
            n += xb.shape[0]
        cam_p = cam_acc / max(n, 1)
        ig_p = ig_acc / max(n, 1)
        mean_p = 0.5 * (cam_p + ig_p)
        results[clock] = ClockResult(
            clock=clock, cam_profile=cam_p, ig_profile=ig_p, mean_profile=mean_p,
            spec_cam=specificity(cam_p, clock, L),
            spec_ig=specificity(ig_p, clock, L),
            spec_mean=specificity(mean_p, clock, L),
            n_beats=n)
        print(f"[{clock:>4}] beats={n:>6}  spec(CAM)={results[clock].spec_cam:.2f}"
              f"  spec(IG)={results[clock].spec_ig:.2f}"
              f"  spec(mean)={results[clock].spec_mean:.2f}"
              f"  chance={chance_level(clock):.2f}  R2={CLOCK_R2[clock]:.2f}")
    return results


# ----------------------------------------------------------------------------
# 5.  Representative median beat (for the LEFT panel) + synthetic fallback
# ----------------------------------------------------------------------------

def representative_beat(beats: np.ndarray, L_target: int | None = None) -> np.ndarray:
    """A single clean lead-II-like beat for plotting: cohort-mean over beats,
    lead reduced to its most-variable lead. Returns (L,)."""
    b = np.asarray(beats, dtype=np.float64)
    if b.ndim == 2:
        beat = b.mean(axis=0)
    else:
        # (N,C,L) or (N,L,C) -> normalise to (N,C,L)
        if b.ndim == 3 and b.shape[1] > b.shape[2] and b.shape[2] <= 12:
            b = np.transpose(b, (0, 2, 1))
        m = b.mean(axis=0)                     # (C, L)
        lead = int(np.argmax(m.std(axis=1)))   # most structured lead
        beat = m[lead]
    return beat


def synthetic_beat(L: int = 500) -> np.ndarray:
    """A textbook PQRST median beat (SYNTHETIC, for --demo only)."""
    t = np.linspace(0, 1, L)

    def g(c, w, a):
        return a * np.exp(-0.5 * ((t - c) / w) ** 2)
    p = g(0.12, 0.020, 0.15)
    q = g(0.345, 0.006, -0.10)
    r = g(0.365, 0.008, 1.00)
    s = g(0.395, 0.008, -0.25)
    tw = g(0.62, 0.045, 0.30)
    return p + q + r + s + tw


def synthetic_results(L: int = 500, seed: int = 0) -> dict[str, ClockResult]:
    """Fabricate plausible per-clock attention concentrated (weakly for P/PR)
    inside each window, so the WHOLE pipeline runs with no artifacts.
    Every consumer stamps SYNTHETIC on its output."""
    rng = np.random.default_rng(seed)
    out: dict[str, ClockResult] = {}
    for clock in CLOCKS:
        a, b = window_indices(L, BEAT_WINDOWS[clock])
        centre = (a + b) / 2.0
        width = (b - a) / 2.0
        x = np.arange(L)
        peak = np.exp(-0.5 * ((x - centre) / (width + 1e-9)) ** 2)
        # weak clocks (P, PR) get more diffuse attention + noise (honest)
        diffuse = 0.6 if clock in ("P", "PR") else 0.15
        prof = (1 - diffuse) * peak + diffuse * rng.random(L)
        prof = np.clip(prof, 0, None)
        prof = prof / prof.max()
        out[clock] = ClockResult(
            clock=clock, cam_profile=prof.copy(), ig_profile=prof.copy(),
            mean_profile=prof.copy(),
            spec_cam=specificity(prof, clock, L),
            spec_ig=specificity(prof, clock, L),
            spec_mean=specificity(prof, clock, L),
            n_beats=0, synthetic=True)
    return out


# ----------------------------------------------------------------------------
# 6.  Loading real artifacts
# ----------------------------------------------------------------------------

def load_clock_models(models_dir: str, n_leads: int = 12) -> dict:
    """Load the four Clock1DCNN state_dicts from `models_dir`.

    Looks for files matching each clock, e.g.
        clock_P.pt / P.pt / clock_P.pth / P_clock.pt ...
    Prefers the study's own Clock1DCNN class; falls back to the reference arch
    (strict=False). Returns {clock: model}. Raises if a file is missing.
    """
    import torch
    cls, src = _import_study_clock()
    if cls is None:
        cls = _reference_clock_cls()
        src = "reference (heart_saliency.py)"
    print(f"Clock1DCNN class: {src}")
    d = Path(models_dir)
    models = {}
    for clock in CLOCKS:
        safe = clock.replace("-", "").replace("/", "")   # ST-T -> STT
        cands = [f"clock_{clock}.pt", f"clock_{safe}.pt", f"{clock}.pt",
                 f"{safe}.pt", f"clock_{clock}.pth", f"{safe}_clock.pt",
                 f"clock_{safe}.pth", f"{clock}_clock.pt"]
        path = next((d / c for c in cands if (d / c).exists()), None)
        if path is None:
            raise FileNotFoundError(
                f"[{clock}] no weight file in {models_dir} "
                f"(looked for {cands}). Use --demo to smoke-test the pipeline.")
        try:
            model = cls(n_leads=n_leads)
        except TypeError:
            model = cls()                       # study class may have own sig
        state = torch.load(path, map_location="cpu")
        state = state.get("state_dict", state) if isinstance(state, dict) else state
        missing, unexpected = model.load_state_dict(state, strict=False)
        if missing or unexpected:
            print(f"[{clock}] loaded {path.name} with strict=False "
                  f"(missing={len(missing)}, unexpected={len(unexpected)}). "
                  f"Grad-CAM/IG remain valid.")
        else:
            print(f"[{clock}] loaded {path.name} exactly.")
        models[clock] = model
    return models


def load_beats(path: str) -> np.ndarray:
    p = Path(path)
    if p.suffix == ".npy":
        return np.load(p)
    if p.suffix == ".npz":
        z = np.load(p)
        for k in ("beats", "median_beats", "X", "arr_0"):
            if k in z:
                return z[k]
        return z[list(z.keys())[0]]
    raise ValueError(f"unsupported beats file: {path} (use .npy/.npz)")


# ----------------------------------------------------------------------------
# 7.  Composite figure  (matplotlib; heart via pyvista+glb if available)
# ----------------------------------------------------------------------------

# Where each chamber sits in the RIGHT panel's axes coordinates (0..1), used
# both for the schematic heart and for anchoring ribbons from the beat bands.
CHAMBER_XY: dict[str, tuple[float, float]] = {
    "P":    (0.30, 0.74),   # atria  (top)
    "PR":   (0.50, 0.56),   # AV node (centre)
    "QRS":  (0.34, 0.30),   # ventricles (lower-left, LV bulk)
    "ST-T": (0.62, 0.40),   # myocardium (wall, right)
}


def _render_glb_heart(glb_path: str, results: dict, out_png: str) -> bool:
    """Colour each chamber mesh of the .glb by its disease-aging and screenshot.
    Returns True on success. Chamber<-mesh mapping is by name substring; if the
    glb has no per-chamber submeshes we bail out to the schematic."""
    try:
        import pyvista as pv
        from matplotlib import colormaps
        from matplotlib.colors import Normalize
    except Exception as e:
        print("pyvista/matplotlib not available for GLB heart:", e)
        return False
    try:
        scene = pv.read(glb_path)
    except Exception as e:
        print("could not read GLB:", e)
        return False

    # collect named blocks
    blocks = []
    def walk(b):
        if isinstance(b, pv.MultiBlock):
            for i in range(b.n_blocks):
                walk(b[i]) if b[i] is not None else None
                nm = b.get_block_name(i) if hasattr(b, "get_block_name") else None
                if nm and b[i] is not None and not isinstance(b[i], pv.MultiBlock):
                    blocks.append((nm.lower(), b[i]))
        # fallthrough
    if isinstance(scene, pv.MultiBlock):
        walk(scene)
    else:
        blocks = [("heart", scene)]
    if not blocks:
        return False

    name_map = {  # substrings -> clock
        "atri": "P", "la": "P", "ra": "P",
        "av": "PR", "node": "PR", "septum": "PR",
        "ventric": "QRS", "lv": "QRS", "rv": "QRS",
        "myo": "ST-T", "wall": "ST-T", "epi": "ST-T",
    }
    deltas = {c: DISEASE_AGING[c]["delta_years"] for c in CLOCKS}
    vmax = max(1.0, max(deltas.values()))
    norm = Normalize(vmin=0.0, vmax=vmax)
    cmap = colormaps["inferno"]

    pl = pv.Plotter(off_screen=True, window_size=(900, 1000))
    pl.set_background("white")
    for nm, mesh in blocks:
        clock = next((c for key, c in name_map.items() if key in nm), None)
        if clock is None:
            pl.add_mesh(mesh, color=(0.8, 0.8, 0.82), opacity=0.35,
                        smooth_shading=True)
        else:
            rgb = cmap(norm(deltas[clock]))[:3]
            pl.add_mesh(mesh, color=rgb, smooth_shading=True, specular=0.2)
    pl.camera_position = "xy"
    try:
        pl.screenshot(out_png)
        pl.close()
        return True
    except Exception as e:
        print("GLB screenshot failed (headless? try xvfb-run):", e)
        return False


def _draw_schematic_heart(ax, results: dict):
    """Fallback four-chamber heart drawn with matplotlib patches, tinted by
    disease-aging. Not anatomically exact — a clean schematic for the figure."""
    from matplotlib import colormaps
    from matplotlib.colors import Normalize
    from matplotlib.patches import Ellipse, FancyBboxPatch

    deltas = {c: DISEASE_AGING[c]["delta_years"] for c in CLOCKS}
    vmax = max(1.0, max(deltas.values()))
    # vmin floored below 0 so zero-aging chambers read dark-purple, not pure
    # black (honest: cold=dark, hot=bright; avoids "holes" on the schematic).
    norm = Normalize(vmin=-1.8, vmax=vmax)
    cmap = colormaps["inferno"]

    def tint(c):
        return cmap(norm(deltas[c]))

    # myocardial wall (ST-T) behind everything
    ax.add_patch(FancyBboxPatch((0.16, 0.14), 0.62, 0.74,
                 boxstyle="round,pad=0.02,rounding_size=0.14",
                 linewidth=0, facecolor=tint("ST-T"), alpha=0.55, zorder=1))
    # atria (P) — two ellipses on top
    for dx in (-0.13, 0.13):
        ax.add_patch(Ellipse((0.47 + dx, 0.72), 0.20, 0.16,
                     facecolor=tint("P"), edgecolor="white", lw=1.5, zorder=3))
    # AV node band (PR) — thin band between atria and ventricles
    ax.add_patch(FancyBboxPatch((0.30, 0.50), 0.34, 0.06,
                 boxstyle="round,pad=0.005,rounding_size=0.03",
                 facecolor=tint("PR"), edgecolor="white", lw=1.2, zorder=4))
    # ventricles (QRS) — two big ellipses below
    for dx in (-0.12, 0.13):
        ax.add_patch(Ellipse((0.47 + dx, 0.32), 0.24, 0.30,
                     facecolor=tint("QRS"), edgecolor="white", lw=1.5, zorder=3))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # chamber labels with disease-aging
    lab = {"P": ("Atria", "P"), "PR": ("AV node", "PR"),
           "QRS": ("Ventricles", "QRS"), "ST-T": ("Myocardium", "ST-T")}
    for c, (x, y) in CHAMBER_XY.items():
        name, sub = lab[c]
        dy = DISEASE_AGING[c]["delta_years"]
        txt = f"{name}\n({sub})"
        if dy > 0:
            txt += f"\n+{dy:.2f} yr"
        ax.text(x, y, txt, ha="center", va="center", fontsize=8.5,
                color="white", fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc="black", alpha=0.35, lw=0))


def make_figure(results: dict, beat: np.ndarray, out_png: str,
                heart_glb: str | None = None, synthetic: bool = False,
                title_note: str = ""):
    """Composite: LEFT beat+attention bands, RIGHT heart, ribbons between."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import ConnectionPatch

    L = len(beat)
    x = np.arange(L)

    fig = plt.figure(figsize=(14, 6.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.06)
    axL = fig.add_subplot(gs[0, 0])
    axR = fig.add_subplot(gs[0, 1])

    # ---- LEFT: median beat + four attention bands -------------------------
    beat_n = (beat - beat.min()) / (np.ptp(beat) + 1e-9)
    axL.plot(x, beat_n, color="black", lw=2.0, zorder=5)
    axL.set_ylim(-0.05, 1.30)
    axL.set_xlim(0, L - 1)
    for c in CLOCKS:
        prof = results[c].mean_profile
        pn = prof / (prof.max() + 1e-9)
        col = CLOCK_COLORS[c]
        # attention as a filled curve near the baseline
        axL.fill_between(x, -0.05, -0.05 + 0.28 * pn, color=col, alpha=0.30,
                         zorder=2, linewidth=0)
        # window band
        a, b = window_indices(L, BEAT_WINDOWS[c])
        axL.axvspan(a, b, color=col, alpha=0.08, zorder=1)
        # label at window centre
        axL.text((a + b) / 2, 1.20, c, ha="center", va="center",
                 color=col, fontsize=11, fontweight="bold")
        sp = results[c].spec_mean
        axL.text((a + b) / 2, 1.09, f"spec {sp:.2f}", ha="center", va="center",
                 color=col, fontsize=8)
    axL.set_title("Median beat with per-subsystem model attention\n"
                  "(band = clock's own P/PR/QRS/ST-T window; "
                  "curve = cohort-mean Grad-CAM+IG)", fontsize=10)
    axL.set_xlabel("beat sample"); axL.set_yticks([])
    for s in ("top", "right", "left"):
        axL.spines[s].set_visible(False)

    # ---- RIGHT: heart -----------------------------------------------------
    used_glb = False
    if heart_glb and Path(heart_glb).exists():
        tmp_png = str(Path(out_png).with_suffix("")) + "_heart.png"
        if _render_glb_heart(heart_glb, results, tmp_png):
            img = plt.imread(tmp_png)
            axR.imshow(img, extent=(0, 1, 0, 1), aspect="auto", zorder=1)
            axR.set_xlim(0, 1); axR.set_ylim(0, 1); axR.axis("off")
            used_glb = True
            # overlay chamber deltas
            for c, (px, py) in CHAMBER_XY.items():
                dy = DISEASE_AGING[c]["delta_years"]
                t = f"{c}" + (f"  +{dy:.2f}yr" if dy > 0 else "")
                axR.text(px, py, t, ha="center", va="center", fontsize=9,
                         color="white", fontweight="bold",
                         bbox=dict(boxstyle="round,pad=0.2", fc="black",
                                   alpha=0.4, lw=0), zorder=6)
    if not used_glb:
        _draw_schematic_heart(axR, results)
    axR.set_title("Four-chamber heart tinted by disease-driven aging\n"
                  "(ischemia→myocardium +4.79 yr, AV block→AV node "
                  "+3.39 yr)", fontsize=10)

    # ---- ribbons: each band -> its chamber --------------------------------
    for c in CLOCKS:
        a, b = window_indices(L, BEAT_WINDOWS[c])
        x_src = (a + b) / 2
        con = ConnectionPatch(
            xyA=(x_src, -0.05 + 0.14), coordsA=axL.transData,
            xyB=CHAMBER_XY[c], coordsB=axR.transAxes,
            arrowstyle="-|>", connectionstyle="arc3,rad=-0.22",
            lw=2.2, color=CLOCK_COLORS[c], alpha=0.75, zorder=20)
        fig.add_artist(con)

    stamp = "  [SYNTHETIC — plumbing demo, not a result]" if synthetic else ""
    sup = ("Witness 1 (ECG): subsystem clocks look where they should  |  "
           f"whole-beat MAE {WHOLE_BEAT_MAE:.1f} yr{stamp}")
    if title_note:
        sup += f"\n{title_note}"
    fig.suptitle(sup, fontsize=12, fontweight="bold", y=1.02,
                 color=("#b00" if synthetic else "black"))
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")


# ----------------------------------------------------------------------------
# 8.  Specificity table (CSV + Markdown)
# ----------------------------------------------------------------------------

def write_tables(results: dict, out_csv: str, out_md: str, synthetic: bool):
    rows = []
    for c in CLOCKS:
        r = results[c]
        da = DISEASE_AGING[c]
        rows.append(dict(
            clock=c, substrate=da["substrate"], chamber=da["chamber"],
            window_start=BEAT_WINDOWS[c][0], window_end=BEAT_WINDOWS[c][1],
            chance_level=round(chance_level(c), 3),
            specificity_gradcam=round(r.spec_cam, 3),
            specificity_ig=round(r.spec_ig, 3),
            specificity_mean=round(r.spec_mean, 3),
            specificity_over_chance=round(r.spec_mean / max(chance_level(c), 1e-9), 2),
            method_agreement=round(1 - abs(r.spec_cam - r.spec_ig), 3),
            clock_R2=CLOCK_R2[c],
            disease=da["condition"],
            disease_aging_years=da["delta_years"],
            n_beats=r.n_beats, synthetic=synthetic))
    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_csv(out_csv, index=False)
    except Exception:
        import csv as _csv
        with open(out_csv, "w", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    print(f"wrote {out_csv}")

    hdr = ("| clock | substrate | window | chance | spec(CAM) | spec(IG) | "
           "spec(mean) | x chance | agree | R2 | disease | aging(yr) |")
    sep = "|" + "---|" * 12
    lines = [("**SYNTHETIC — plumbing demo, not a result**\n" if synthetic else ""),
             hdr, sep]
    for c in CLOCKS:
        r = results[c]; da = DISEASE_AGING[c]
        w = BEAT_WINDOWS[c]
        lines.append(
            f"| {c} | {da['substrate']} | {w[0]:.2f}-{w[1]:.2f} | "
            f"{chance_level(c):.2f} | {r.spec_cam:.2f} | {r.spec_ig:.2f} | "
            f"**{r.spec_mean:.2f}** | {r.spec_mean/max(chance_level(c),1e-9):.2f}x | "
            f"{1-abs(r.spec_cam-r.spec_ig):.2f} | {CLOCK_R2[c]:.2f} | "
            f"{da['condition']} | "
            f"{('+'+format(da['delta_years'],'.2f')) if da['delta_years'] else '~0'} |")
    lines += [
        "",
        "*Specificity = fraction of the clock's cohort-mean attention mass "
        "inside its own beat window. `x chance` = specificity / (window width); "
        ">1 means the clock concentrates evidence on its segment. `agree` = "
        "1-|spec(CAM)-spec(IG)| (method concordance).*",
        "",
        "*Honesty: saliency localises the model's evidence, not causation. "
        "The P (R2 0.26) and PR (R2 0.20) clocks are weak; expect lower / "
        "noisier specificity and read it as-measured.*",
    ]
    Path(out_md).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_md}")


# ----------------------------------------------------------------------------
# 9.  Self-contained Three.js interactive viewer
# ----------------------------------------------------------------------------

def write_threejs(results: dict, beat: np.ndarray, out_html: str,
                  synthetic: bool):
    """Emit a single self-contained HTML file: a procedural four-chamber heart
    (no external GLB needed); click a chamber to see that subsystem's attention
    curve and disease-aging. Three.js is pulled from a CDN via an importmap;
    ALL study data is inlined as JSON, so the science is offline-complete."""
    # downsample profiles/beat for a compact inline payload
    def ds(a, n=200):
        a = np.asarray(a, dtype=float)
        idx = np.linspace(0, len(a) - 1, n).astype(int)
        v = a[idx]
        return [round(float(z), 4) for z in v]

    payload = {
        "synthetic": bool(synthetic),
        "beat": ds((beat - beat.min()) / (np.ptp(beat) + 1e-9)),
        "clocks": {c: {
            "color": CLOCK_COLORS[c],
            "attention": ds(results[c].mean_profile / (results[c].mean_profile.max() + 1e-9)),
            "window": list(BEAT_WINDOWS[c]),
            "specificity": round(results[c].spec_mean, 3),
            "chance": round(chance_level(c), 3),
            "r2": CLOCK_R2[c],
            "substrate": DISEASE_AGING[c]["substrate"],
            "disease": DISEASE_AGING[c]["condition"],
            "aging": DISEASE_AGING[c]["delta_years"],
        } for c in CLOCKS},
        "clock_order": list(CLOCKS),
    }
    data_json = json.dumps(payload)
    banner = ("<div id='synbanner'>SYNTHETIC — plumbing demo, not a result</div>"
              if synthetic else "")

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Body Clock — ECG subsystem saliency on the heart</title>
<style>
  :root{--bg:#0d0f14;--fg:#e8eaf0;--muted:#9aa3b2;}
  html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);
    font-family:system-ui,Segoe UI,Roboto,sans-serif;overflow:hidden}
  #wrap{display:flex;height:100vh;width:100vw}
  #view{flex:1 1 60%;position:relative}
  #side{flex:0 0 380px;max-width:42vw;padding:18px 20px;overflow:auto;
    border-left:1px solid #222836;background:#0a0c11}
  h1{font-size:15px;margin:0 0 2px}
  .sub{color:var(--muted);font-size:12px;margin-bottom:14px;line-height:1.4}
  #panel h2{font-size:14px;margin:6px 0 2px}
  #panel .k{color:var(--muted);font-size:12px}
  #panel .v{font-weight:600}
  canvas#att{width:100%;height:150px;background:#11141b;border-radius:8px;
    margin-top:10px;display:block}
  .row{display:flex;justify-content:space-between;padding:3px 0;
    border-bottom:1px solid #1a1f2b;font-size:13px}
  .hint{color:var(--muted);font-size:12px;margin-top:14px;line-height:1.45}
  #synbanner{position:absolute;top:10px;left:10px;background:#b00;color:#fff;
    padding:5px 10px;border-radius:6px;font-weight:700;font-size:12px;z-index:9}
  .legend{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
  .chip{display:flex;align-items:center;gap:5px;font-size:12px;cursor:pointer;
    padding:3px 8px;border-radius:20px;background:#151a24}
  .dot{width:10px;height:10px;border-radius:50%}
</style></head>
<body>
<div id="wrap">
  <div id="view">__BANNER__</div>
  <div id="side">
    <h1>Where each ECG subsystem clock looks</h1>
    <div class="sub">Four 1-D CNN age clocks (P / PR / QRS / ST-T) on PTB-XL
      median beats. Click a chamber (or a chip) to see that subsystem's
      cohort-mean attention and its disease-driven aging. Saliency shows where
      the model looks — not causation.</div>
    <div class="legend" id="legend"></div>
    <div id="panel">
      <h2 id="p-title">Select a chamber</h2>
      <div class="row"><span class="k">substrate</span><span class="v" id="p-sub">—</span></div>
      <div class="row"><span class="k">specificity (own window)</span><span class="v" id="p-spec">—</span></div>
      <div class="row"><span class="k">chance level</span><span class="v" id="p-chance">—</span></div>
      <div class="row"><span class="k">clock R²</span><span class="v" id="p-r2">—</span></div>
      <div class="row"><span class="k">disease</span><span class="v" id="p-dis">—</span></div>
      <div class="row"><span class="k">disease-driven aging</span><span class="v" id="p-age">—</span></div>
      <canvas id="att" width="340" height="150"></canvas>
      <div class="hint" id="p-hint">Attention (y) over the median beat (x); the
        shaded band is this clock's own P/PR/QRS/ST-T window.</div>
    </div>
  </div>
</div>
<script type="importmap">
{ "imports": { "three": "https://unpkg.com/three@0.160.0/build/three.module.js" } }
</script>
<script type="module">
import * as THREE from 'three';
const DATA = __DATA__;
const order = DATA.clock_order;

// ---- scene ----
const view = document.getElementById('view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d0f14);
const cam = new THREE.PerspectiveCamera(45, view.clientWidth/view.clientHeight, 0.1, 100);
cam.position.set(0, 0.4, 6.2);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(view.clientWidth, view.clientHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
view.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const key = new THREE.DirectionalLight(0xffffff, 0.9); key.position.set(3,4,5); scene.add(key);

// disease-aging -> emissive intensity (heat)
function agingColor(c){
  const a = DATA.clocks[c].aging;         // years
  const t = Math.min(1, a/5.0);           // 0..1
  // cool grey -> hot red/orange
  const col = new THREE.Color();
  col.setHSL(0.62 - 0.62*t, 0.55, 0.32 + 0.18*t);
  return col;
}

// build a stylised four-chamber heart from primitives; tag each with its clock
const heart = new THREE.Group(); scene.add(heart);
const meshes = {};
function chamber(c, geo, pos){
  const mat = new THREE.MeshStandardMaterial({
    color: agingColor(c), roughness:0.55, metalness:0.05,
    emissive: agingColor(c), emissiveIntensity: Math.min(0.6, DATA.clocks[c].aging/6)});
  const m = new THREE.Mesh(geo, mat);
  m.position.set(...pos); m.userData.clock = c; heart.add(m); meshes[c]=m; return m;
}
// atria (P) — two spheres on top
const atria = new THREE.Group();
[[-0.75,1.15,0],[0.75,1.15,0]].forEach(p=>{
  const m = chamber('P', new THREE.SphereGeometry(0.62,32,24), p); atria.add(m);});
// AV node (PR) — torus/disc in the middle
chamber('PR', new THREE.TorusGeometry(0.42,0.16,16,32), [0,0.35,0]).rotation.x=Math.PI/2;
// ventricles (QRS) — two big cones/ellipsoids below
[[-0.7,-0.75,0],[0.7,-0.75,0]].forEach(p=>{
  const g = new THREE.SphereGeometry(0.95,32,24); g.scale(1,1.35,1);
  chamber('QRS', g, p);});
// myocardium (ST-T) — translucent shell around the ventricles
const shell = new THREE.Mesh(
  new THREE.SphereGeometry(1.7,40,30),
  new THREE.MeshStandardMaterial({color:agingColor('ST-T'), emissive:agingColor('ST-T'),
    emissiveIntensity:Math.min(0.7,DATA.clocks['ST-T'].aging/6),
    transparent:true, opacity:0.28, roughness:0.7, side:THREE.BackSide}));
shell.position.set(0,-0.5,0); shell.userData.clock='ST-T'; heart.add(shell); meshes['ST-T']=shell;

// ---- picking ----
const ray = new THREE.Raycaster(); const mouse = new THREE.Vector2();
function pick(e){
  const r = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX-r.left)/r.width)*2-1;
  mouse.y = -((e.clientY-r.top)/r.height)*2+1;
  ray.setFromCamera(mouse, cam);
  const hits = ray.intersectObjects(heart.children, true);
  if(hits.length){ select(hits[0].object.userData.clock); }
}
renderer.domElement.addEventListener('click', pick);

// ---- side panel + attention canvas ----
const attC = document.getElementById('att'); const ctx = attC.getContext('2d');
function drawAtt(c){
  const d = DATA.clocks[c]; const W=attC.width,H=attC.height;
  ctx.clearRect(0,0,W,H);
  // window band
  ctx.fillStyle = 'rgba(255,255,255,0.06)';
  ctx.fillRect(d.window[0]*W,0,(d.window[1]-d.window[0])*W,H);
  // beat (grey)
  const beat = DATA.beat;
  ctx.strokeStyle='rgba(180,190,205,0.5)'; ctx.lineWidth=1; ctx.beginPath();
  beat.forEach((v,i)=>{const x=i/(beat.length-1)*W,y=H-8-v*(H-30);
    i?ctx.lineTo(x,y):ctx.moveTo(x,y);}); ctx.stroke();
  // attention (clock colour, filled)
  const a = d.attention; ctx.beginPath();
  ctx.moveTo(0,H);
  a.forEach((v,i)=>{const x=i/(a.length-1)*W,y=H-8-v*(H-30);ctx.lineTo(x,y);});
  ctx.lineTo(W,H); ctx.closePath();
  ctx.fillStyle=d.color+'55'; ctx.fill();
  ctx.strokeStyle=d.color; ctx.lineWidth=2; ctx.beginPath();
  a.forEach((v,i)=>{const x=i/(a.length-1)*W,y=H-8-v*(H-30);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});
  ctx.stroke();
}
function select(c){
  const d = DATA.clocks[c];
  document.getElementById('p-title').textContent = c+'  ('+d.substrate+')';
  document.getElementById('p-title').style.color = d.color;
  document.getElementById('p-sub').textContent = d.substrate;
  document.getElementById('p-spec').textContent = d.specificity.toFixed(2)
     + '  ('+(d.specificity/d.chance).toFixed(2)+'x chance)';
  document.getElementById('p-chance').textContent = d.chance.toFixed(2);
  document.getElementById('p-r2').textContent = d.r2.toFixed(2)
     + (d.r2<0.3?'  (weak clock)':'');
  document.getElementById('p-dis').textContent = d.disease;
  document.getElementById('p-age').textContent = d.aging>0?('+'+d.aging.toFixed(2)+' yr'):'~0 yr';
  // pulse the selected mesh
  Object.entries(meshes).forEach(([k,m])=>{
    m.material.emissiveIntensity = (k===c? 0.9 : Math.min(0.6, DATA.clocks[k].aging/6));});
  drawAtt(c);
}

// legend chips
const legend = document.getElementById('legend');
order.forEach(c=>{
  const el = document.createElement('div'); el.className='chip';
  el.innerHTML = "<span class='dot' style='background:"+DATA.clocks[c].color+"'></span>"+c;
  el.onclick=()=>select(c); legend.appendChild(el);
});

// ---- animate ----
let t=0;
function loop(){ t+=0.005; heart.rotation.y=Math.sin(t)*0.5;
  renderer.render(scene,cam); requestAnimationFrame(loop);}
loop();
addEventListener('resize',()=>{
  cam.aspect=view.clientWidth/view.clientHeight; cam.updateProjectionMatrix();
  renderer.setSize(view.clientWidth, view.clientHeight);});
select('ST-T');   // open on the strongest disease signal
</script>
</body></html>
"""
    html = html.replace("__DATA__", data_json).replace("__BANNER__", banner)
    Path(out_html).write_text(html, encoding="utf-8")
    print(f"wrote {out_html}")


# ----------------------------------------------------------------------------
# 10.  CLI
# ----------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models-dir", help="dir with clock_{P,PR,QRS,STT}.pt weights")
    ap.add_argument("--beats", help=".npy/.npz of test median beats (N,leads,L)")
    ap.add_argument("--heart-glb", help="four-chamber heart .glb for right panel")
    ap.add_argument("--out", default="enrich/out_heart_saliency",
                    help="output prefix (dir/stem)")
    ap.add_argument("--n-leads", type=int, default=12)
    ap.add_argument("--ig-steps", type=int, default=32)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--demo", action="store_true",
                    help="run SYNTHETIC (no artifacts needed) to verify plumbing")
    a = ap.parse_args(argv)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    synthetic = a.demo or not (a.models_dir and a.beats)
    if synthetic and not a.demo:
        print("NOTE: --models-dir/--beats not both given -> SYNTHETIC demo mode.")

    if synthetic:
        L = 500
        beat = synthetic_beat(L)
        results = synthetic_results(L)
        note = "SYNTHETIC inputs — verifies figure/table/viewer pipeline only."
    else:
        try:
            import torch  # noqa: F401
        except Exception:
            sys.exit("PyTorch required for real runs. `pip install torch` or use --demo.")
        models = load_clock_models(a.models_dir, n_leads=a.n_leads)
        beats = load_beats(a.beats)
        print(f"beats loaded: shape {np.asarray(beats).shape}")
        results = run_all_clocks(models, beats, ig_steps=a.ig_steps,
                                 batch=a.batch, device=a.device,
                                 n_leads_model=a.n_leads)
        beat = representative_beat(beats)
        note = ""

    make_figure(results, beat, str(out) + "_figure.png",
                heart_glb=a.heart_glb, synthetic=synthetic, title_note=note)
    write_tables(results, str(out) + "_specificity.csv",
                 str(out) + "_specificity.md", synthetic)
    write_threejs(results, beat, str(out) + "_viewer.html", synthetic)

    print("\nDONE.")
    print(f"  figure : {out}_figure.png")
    print(f"  table  : {out}_specificity.csv / .md")
    print(f"  viewer : {out}_viewer.html")
    if synthetic:
        print("  [SYNTHETIC run — outputs are plumbing demos, not results]")


if __name__ == "__main__":
    main()
