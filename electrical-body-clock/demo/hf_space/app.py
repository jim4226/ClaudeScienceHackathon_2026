"""
HeartVector live demo — From Clocks to Coordinates.

Two tabs:
  1. Live inference: build (or upload) a 12-lead ECG, run the five FROZEN
     subsystem phase-age clocks on CPU, and read out the A / D geometry
     (shared aging axis vs cross-subsystem disagreement) exactly as in the paper.
  2. Result explorer: the frozen result figures (perturbation compass, external
     Chapman transport, multiscale organ atlas, brain-MRI disagreement, and the
     MotionVector structure-function boundary test).

Research demonstration only — not a medical device, not for clinical use.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import gradio as gr

import inference as inf

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")

PHASE_LABEL = {"global": "Whole-ECG", "P": "P (atrial)", "AV": "AV (PR)",
               "QRS": "QRS (depol.)", "STT": "ST-T (repol.)"}
BLUE, RED, GREY = "#1f5fa8", "#c0392b", "#9aa0a6"


# ----------------------------------------------------------------------------- plots
def plot_fingerprint(res, age):
    """Radar of the four subsystem phase-age GAPS (phase age minus chronological)."""
    subs = ["P", "AV", "QRS", "STT"]
    gaps = [res["phase_ages"][s] - age for s in subs]
    ang = np.linspace(0, 2 * np.pi, len(subs), endpoint=False)
    ang = np.concatenate([ang, ang[:1]]); vals = gaps + gaps[:1]
    fig, ax = plt.subplots(figsize=(3.6, 3.6), subplot_kw=dict(projection="polar"))
    lim = max(10, np.max(np.abs(gaps)) * 1.25)
    ax.plot(ang, vals, color=BLUE, lw=2)
    ax.fill(ang, vals, color=BLUE, alpha=0.20)
    ax.plot(np.linspace(0, 2 * np.pi, 200), [0] * 200, color=GREY, lw=0.8, ls="--")
    ax.set_xticks(ang[:-1]); ax.set_xticklabels([PHASE_LABEL[s] for s in subs], fontsize=8)
    ax.set_ylim(-lim, lim); ax.set_yticks([-lim/2, 0, lim/2])
    ax.set_yticklabels([f"{-lim/2:.0f}", "0", f"+{lim/2:.0f}"], fontsize=6)
    ax.set_title("Subsystem age-gap fingerprint\n(years vs chronological)", fontsize=9, pad=14)
    fig.tight_layout()
    return fig


def plot_beat(res):
    """Median beat (lead II) with the four subsystem windows shaded."""
    med = res["median_beat"]; wins = res["wins"]
    lead = med[:, 1] if med.shape[1] > 1 else med[:, 0]
    x = np.arange(len(lead))
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.plot(x, lead, color="#222", lw=1.2, zorder=3)
    cols = {"P": "#4C9F70", "PR": "#E0A458", "QRS": BLUE, "STT": RED}
    for k, c in cols.items():
        if k in wins:
            lo, hi = wins[k]; ax.axvspan(lo, hi, color=c, alpha=0.18, zorder=1)
            ax.text((lo + hi) / 2, ax.get_ylim()[1], k, color=c, fontsize=7,
                    ha="center", va="top", fontweight="bold")
    ax.set_title("Median beat (lead II) with subsystem windows", fontsize=9)
    ax.set_xlabel("sample @ 500 Hz", fontsize=8); ax.set_yticks([])
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig


def plot_geometry(res):
    """Where this record sits in the A (shared axis) vs D (disagreement) plane."""
    A, D = res["A_std"], res["D_std"]
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    # reference cloud: standard normal-ish backdrop for context
    rng = np.random.default_rng(0)
    ax.scatter(rng.normal(0, 1, 1500), np.abs(rng.normal(0, 1, 1500)) * 0.7,
               s=4, c=GREY, alpha=0.15, lw=0, zorder=1)
    ax.axvline(0, color="#ccc", lw=0.8, zorder=1)
    ax.scatter([A], [D], s=140, c=RED, edgecolor="k", lw=1.0, zorder=4, marker="*")
    ax.annotate(f"  this ECG\n  A={A:+.2f}, D={D:+.2f}", (A, D), fontsize=8,
                color=RED, va="center")
    ax.set_xlabel("A  — shared aging axis (z)", fontsize=8)
    ax.set_ylabel("D  — cross-subsystem disagreement (z)", fontsize=8)
    ax.set_title("Position in the age–state plane", fontsize=9)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig


def _readout(res, age, sex, qa):
    pa = res["phase_ages"]
    sx = "female" if int(sex) == 1 else "male"
    lines = [
        f"### Frozen clocks (chronological age {age:.0f} y, {sx})",
        "",
        "| Subsystem | Phase-age (y) | Gap vs age (y) |",
        "|---|--:|--:|",
    ]
    for s in ["global", "P", "AV", "QRS", "STT"]:
        lines.append(f"| {PHASE_LABEL[s]} | {pa[s]:.1f} | {pa[s]-age:+.1f} |")
    lines += [
        "",
        f"**Shared aging axis A** = `{res['A_std']:+.3f}` (z)  ·  "
        f"**Disagreement radius D** = `{res['D_std']:+.3f}` (z)",
        "",
        f"Whitened contrast q = ({res['q'][0]:+.2f}, {res['q'][1]:+.2f}, {res['q'][2]:+.2f})",
        "",
        f"<sub>beats used: {qa.get('n_beats_used','?')} · R-peaks: {qa.get('n_rpeaks','?')} "
        f"· delineation ok: {qa.get('deline_ok','?')}</sub>",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- callbacks
def run_synth(heart_rate, age, sex_label, stt_shift, qrs_widen, seed):
    sex = 1 if sex_label == "female" else 0
    sig = inf.synth_12lead(heart_rate=heart_rate, seed=int(seed),
                           stt_shift=stt_shift, qrs_widen=qrs_widen)
    res, qa = inf.score_signal(sig, fs=500, age=age, sex=sex)
    if res is None:
        msg = f"Inference failed at beat extraction: `{qa.get('reason','unknown')}`. Try a different heart rate/seed."
        return msg, None, None, None
    return (_readout(res, age, sex, qa),
            plot_fingerprint(res, age), plot_beat(res), plot_geometry(res))


def run_upload(file, age, sex_label):
    if file is None:
        return "Upload a WFDB `.hea` (with its `.dat`) or a 12-column CSV.", None, None, None
    sex = 1 if sex_label == "female" else 0
    try:
        sig, fs = inf.parse_uploaded(file.name)
    except Exception as e:
        return f"Could not read file: `{e}`", None, None, None
    res, qa = inf.score_signal(sig, fs=fs, age=age, sex=sex)
    if res is None:
        return f"Inference failed: `{qa.get('reason','unknown')}`.", None, None, None
    return (_readout(res, age, sex, qa),
            plot_fingerprint(res, age), plot_beat(res), plot_geometry(res))


# ------------------------------------------------------------------------------- figures
FIGURES = [
    ("fig_perturbation_compass.png",
     "**Perturbation compass.** A frozen, IKr-aligned perturbation direction recovered from a "
     "randomized dofetilide challenge (blue, tightly clustered) versus a diffuse ischemia direction "
     "(orange). Panels b/c: treatment-arm projections and the signed-vs-unsigned geometry."),
    ("fig_chapman_transport.png",
     "**External transport (Chapman–Shaoxing/Ningbo, n=44,550).** The frozen IKr direction adds "
     "conditional information about QT-extension as intervals/A/D are adjusted (a suppression pattern); "
     "site-stratified estimates and post-hoc rhythm-exclusion sensitivities."),
    ("fig1_disagreement_headline.png",
     "**Brain-MRI disagreement (LEMON, n=220).** Four independent structural aging views; older brains "
     "show larger cross-view disagreement D (p=4.3×10⁻⁸, d=0.84) — a brain-scale echo of the same "
     "shared-axis-vs-disagreement question."),
    ("fig3_segmentation_overlays.png",
     "**Real LEMON anatomy.** Deep tissue segmentation and DKT parcellation on raw T1 (MP2RAGE) for a "
     "young (28 y) and an older (77 y) subject; ventricle/brain ratio 0.009 vs 0.045."),
    ("fig5_atlas.png",
     "**Multiscale organ atlas (NHANES, n=14,362).** The A/D decomposition read across six blood-panel "
     "organ-system clocks; A_body and D_body each add mortality discrimination (secondary, non-confirmatory)."),
    ("fig_s4_motionvector.png",
     "**MotionVector boundary test (NHANES DXA + accelerometry, n=2,891).** A prespecified negative: "
     "compressing 7-day movement into a chronological-age residual destroys the functional signal raw "
     "movement carries — a boundary that motivates a mixed state-space rather than 'everything is an age clock.'"),
]


def show_figure(idx):
    fn, cap = FIGURES[idx]
    return os.path.join(FIGDIR, fn), cap


# ------------------------------------------------------------------------------------ UI
INTRO = """
# From Clocks to Coordinates — HeartVector live demo
**Biological age is a direction, not a single number.** This demo runs the five *frozen*
subsystem phase-age clocks (whole-ECG, P, AV, QRS, ST-T) on a 12-lead ECG and reads out two
coordinates: the **shared aging axis A** (how old the ECG looks overall) and the
**disagreement radius D** (how much the subsystem clocks disagree). Weights and all
standardization constants are frozen from the manuscript — nothing is refit here.

*Research demonstration only. Not a medical device; not for clinical or diagnostic use.*
"""


def build():
    with gr.Blocks(title="HeartVector — From Clocks to Coordinates", theme=gr.themes.Soft()) as demo:
        gr.Markdown(INTRO)
        with gr.Tab("Live inference"):
            with gr.Tabs():
                with gr.Tab("Synthesize an ECG"):
                    gr.Markdown("Build a physiologically-plausible synthetic 12-lead ECG "
                                "(no patient data) and score it live on CPU.")
                    with gr.Row():
                        with gr.Column(scale=1):
                            hr = gr.Slider(40, 140, 70, step=1, label="Heart rate (bpm)")
                            age = gr.Slider(20, 90, 55, step=1, label="Chronological age (y)")
                            sex = gr.Radio(["male", "female"], value="male", label="Sex")
                            stt = gr.Slider(0, 1, 0, step=0.05, label="ST-T drift (illustrative)")
                            qrs = gr.Slider(0, 1, 0, step=0.05, label="QRS widening (illustrative)")
                            seed = gr.Slider(0, 50, 1, step=1, label="Random seed")
                            go = gr.Button("Run frozen clocks", variant="primary")
                        with gr.Column(scale=2):
                            out_md = gr.Markdown()
                    with gr.Row():
                        f_fp = gr.Plot(label="Fingerprint")
                        f_beat = gr.Plot(label="Median beat")
                        f_geo = gr.Plot(label="A–D geometry")
                    go.click(run_synth, [hr, age, sex, stt, qrs, seed],
                             [out_md, f_fp, f_beat, f_geo])
                with gr.Tab("Upload your own"):
                    gr.Markdown("Upload a WFDB record (`.hea` with its `.dat`) or a 12-column CSV "
                                "(canonical lead order I, II, III, aVR, aVL, aVF, V1–V6; samples in rows).")
                    with gr.Row():
                        with gr.Column(scale=1):
                            up = gr.File(label="ECG file (.hea / .csv)")
                            u_age = gr.Slider(20, 90, 55, step=1, label="Chronological age (y)")
                            u_sex = gr.Radio(["male", "female"], value="male", label="Sex")
                            u_go = gr.Button("Run frozen clocks", variant="primary")
                        with gr.Column(scale=2):
                            u_md = gr.Markdown()
                    with gr.Row():
                        u_fp = gr.Plot(label="Fingerprint")
                        u_beat = gr.Plot(label="Median beat")
                        u_geo = gr.Plot(label="A–D geometry")
                    u_go.click(run_upload, [up, u_age, u_sex], [u_md, u_fp, u_beat, u_geo])
        with gr.Tab("Result explorer"):
            gr.Markdown("The frozen result figures behind *From Clocks to Coordinates*. "
                        "Select a result to view it with its caption.")
            names = [f"{i+1}. {FIGURES[i][1].split('.**')[0].replace('**','')}"
                     for i in range(len(FIGURES))]
            sel = gr.Radio(names, value=names[0], type="index", label="Result")
            img = gr.Image(label="", show_label=False)
            cap = gr.Markdown()
            sel.change(show_figure, sel, [img, cap])
            demo.load(lambda: show_figure(0), None, [img, cap])
    return demo


if __name__ == "__main__":
    build().launch()
