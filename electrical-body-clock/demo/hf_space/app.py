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
    """Signed horizontal bar chart of the four subsystem phase-age GAPS.

    A signed bar chart (not a radar) is used deliberately: radar/polar area
    encodings distort *signed* quantities (negative gaps wrap toward the centre
    and read as small-positive), whereas a diverging bar reads sign and magnitude
    directly against a zero line.
    """
    subs = ["P", "AV", "QRS", "STT"]
    gaps = np.array([res["phase_ages"][s] - age for s in subs], float)
    y = np.arange(len(subs))[::-1]                       # top-to-bottom P,AV,QRS,STT
    colors = [RED if g > 0 else BLUE for g in gaps]      # older-than-age vs younger
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.barh(y, gaps, color=colors, edgecolor="k", lw=0.6, height=0.62, zorder=3)
    ax.axvline(0, color="#444", lw=1.0, zorder=2)
    lim = max(8.0, float(np.max(np.abs(gaps))) * 1.30)
    ax.set_xlim(-lim, lim)
    ax.set_yticks(y); ax.set_yticklabels([PHASE_LABEL[s] for s in subs], fontsize=9)
    for yi, g in zip(y, gaps):
        ax.text(g + np.sign(g) * lim * 0.03, yi, f"{g:+.1f}",
                va="center", ha="left" if g >= 0 else "right", fontsize=8,
                color=RED if g > 0 else BLUE, fontweight="bold")
    ax.set_xlabel("phase-age gap (years vs chronological)", fontsize=8)
    ax.set_title("Subsystem age-gap fingerprint\n"
                 r"$\it{red\ =\ older\ than\ age\ \cdot\ blue\ =\ younger\ than\ age}$",
                 fontsize=9)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
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
    """Where this record sits in the A (shared axis) vs D (disagreement) plane.

    The backdrop is the FROZEN calibration reference frame, not a simulated cloud:
    A_std and D_std are z-scores against the calibration partition (mean 0, SD 1
    by construction), so the reference is drawn as labeled 0 / +-1 / +-2 SD guides
    rather than fabricated points.
    """
    A, D = res["A_std"], res["D_std"]
    fig, ax = plt.subplots(figsize=(3.8, 3.6))
    lim = max(3.0, abs(A) + 0.6, abs(D) + 0.6)
    # concentric SD guides on the standardized frame (real reference, not points)
    for r in (1, 2, 3):
        ax.axvline(r, color="#e3e3e3", lw=0.7, zorder=1)
        ax.axvline(-r, color="#e3e3e3", lw=0.7, zorder=1)
        ax.axhline(r, color="#e3e3e3", lw=0.7, zorder=1)
    ax.axvline(0, color="#888", lw=1.0, zorder=2)
    ax.axhline(0, color="#888", lw=1.0, zorder=2)
    ax.text(0.02, lim*0.96, "calibration reference: mean 0, SD 1", fontsize=6.5,
            color=GREY, va="top")
    ax.scatter([A], [D], s=150, c=RED, edgecolor="k", lw=1.0, zorder=4, marker="*")
    ax.annotate(f"  this ECG\n  A={A:+.2f}, D={D:+.2f}", (A, D), fontsize=8,
                color=RED, va="center")
    ax.set_xlim(-lim, lim); ax.set_ylim(min(-0.5, D - 0.6), lim)
    ax.set_xlabel("A  — shared aging axis (SD from reference)", fontsize=8)
    ax.set_ylabel("D  — cross-subsystem disagreement (SD)", fontsize=8)
    ax.set_title("Position in the calibration reference frame", fontsize=9)
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
SYNTH_WARN = (
    "> ⚠️ **Interface illustration only.** This trace is synthetic — a rendering "
    "aid to exercise the controls and plots, **not** a biophysical heart model. "
    "The clocks are running on out-of-distribution input, so any age below is an "
    "artefact of the interface, **not a biological measurement**. For real output, "
    "use the **Real example ECGs** tab or upload a record.\n\n")


def run_synth(heart_rate, age, sex_label, stt_shift, seed):
    sex = 1 if sex_label == "female" else 0
    sig = inf.synth_12lead(heart_rate=heart_rate, seed=int(seed), stt_shift=stt_shift)
    res, qa = inf.score_signal(sig, fs=500, age=age, sex=sex)
    if res is None:
        msg = f"Inference failed at beat extraction: `{qa.get('reason','unknown')}`. Try a different heart rate/seed."
        return msg, None, None, None
    return (SYNTH_WARN + _readout(res, age, sex, qa),
            plot_fingerprint(res, age), plot_beat(res), plot_geometry(res))


def run_example(record_label, age, sex_label):
    """Score a bundled real PTB-XL example record (CC-BY 4.0, attributed)."""
    import json
    exdir = os.path.join(HERE, "examples")
    manifest = {f"{m['record']} (age {m['age']}, {m['sex']})": m
                for m in json.load(open(os.path.join(exdir, "examples_manifest.json")))}
    m = manifest.get(record_label)
    if m is None:
        return "Select an example record.", None, None, None
    # use the record's own age/sex (real metadata), not the sliders
    age, sex = float(m["age"]), (1 if m["sex"] == "F" else 0)
    try:
        sig, fs = inf.parse_uploaded(os.path.join(exdir, m["record"] + ".hea"))
    except Exception as e:
        return f"Could not read example: `{e}`", None, None, None
    res, qa = inf.score_signal(sig, fs=fs, age=age, sex=sex)
    if res is None:
        return f"Inference failed: `{qa.get('reason','unknown')}`.", None, None, None
    head = (f"> **Real PTB-XL record `{m['record']}`** (CC-BY 4.0) — "
            f"{m['label']}, age {m['age']}, sex {m['sex']}.\n\n")
    return (head + _readout(res, age, sex, qa),
            plot_fingerprint(res, age), plot_beat(res), plot_geometry(res))


def run_upload(file, age, sex_label, csv_fs):
    if file is None:
        return "Upload a WFDB record (`.hea` **and** its `.dat`) or a 12-column CSV.", None, None, None
    sex = 1 if sex_label == "female" else 0
    try:
        sig, fs = inf.parse_uploaded(file.name, csv_fs=int(csv_fs))
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


def _example_labels():
    import json
    exdir = os.path.join(HERE, "examples")
    return [f"{m['record']} (age {m['age']}, {m['sex']})"
            for m in json.load(open(os.path.join(exdir, "examples_manifest.json")))]


def build():
    with gr.Blocks(title="HeartVector — From Clocks to Coordinates", theme=gr.themes.Soft()) as demo:
        gr.Markdown(INTRO)
        with gr.Tab("Live inference"):
            with gr.Tabs():
                # DEFAULT tab: real, licensed example ECGs
                with gr.Tab("Real example ECGs"):
                    gr.Markdown("Score a **real 12-lead ECG** bundled from PTB-XL "
                                "(CC-BY 4.0, attributed in `examples/ATTRIBUTION.md`). "
                                "Each record uses its own recorded age and sex.")
                    ex_labels = _example_labels()
                    with gr.Row():
                        with gr.Column(scale=1):
                            ex_sel = gr.Radio(ex_labels, value=ex_labels[0], label="Example record")
                            ex_go = gr.Button("Run frozen clocks", variant="primary")
                        with gr.Column(scale=2):
                            e_md = gr.Markdown()
                    with gr.Row():
                        e_fp = gr.Plot(label="Fingerprint")
                        e_beat = gr.Plot(label="Median beat")
                        e_geo = gr.Plot(label="A–D geometry")
                    ex_go.click(run_example, [ex_sel, gr.State(0), gr.State("male")],
                                [e_md, e_fp, e_beat, e_geo])
                    demo.load(lambda: run_example(ex_labels[0], 0, "male"),
                              None, [e_md, e_fp, e_beat, e_geo])
                with gr.Tab("Upload your own"):
                    gr.Markdown("Upload a WFDB record (`.hea` **with** its `.dat`) or a 12-column CSV "
                                "(canonical lead order I, II, III, aVR, aVL, aVF, V1–V6; samples in "
                                "rows; millivolts). WFDB leads are reordered from the header; a CSV has "
                                "no header, so set its sampling rate below.")
                    with gr.Row():
                        with gr.Column(scale=1):
                            up = gr.File(label="ECG file (.hea + .dat, or .csv)")
                            u_fs = gr.Number(value=500, label="CSV sampling rate (Hz) — ignored for WFDB", precision=0)
                            u_age = gr.Slider(20, 90, 55, step=1, label="Chronological age (y)")
                            u_sex = gr.Radio(["male", "female"], value="male", label="Sex")
                            u_go = gr.Button("Run frozen clocks", variant="primary")
                        with gr.Column(scale=2):
                            u_md = gr.Markdown()
                    with gr.Row():
                        u_fp = gr.Plot(label="Fingerprint")
                        u_beat = gr.Plot(label="Median beat")
                        u_geo = gr.Plot(label="A–D geometry")
                    u_go.click(run_upload, [up, u_age, u_sex, u_fs], [u_md, u_fp, u_beat, u_geo])
                # Synthetic is LAST and clearly labeled as an interface illustration
                with gr.Tab("Synthetic (interface illustration)"):
                    gr.Markdown("⚠️ **Interface illustration only — not a biological result.** "
                                "This builds a synthetic 12-lead trace so the controls and plots can "
                                "be exercised without a record. The clocks run on out-of-distribution "
                                "input; the ages shown are interface artefacts. The ST-T drift control "
                                "perturbs **only** the ST-T segment.")
                    with gr.Row():
                        with gr.Column(scale=1):
                            hr = gr.Slider(40, 140, 70, step=1, label="Heart rate (bpm)")
                            age = gr.Slider(20, 90, 55, step=1, label="Chronological age (y)")
                            sex = gr.Radio(["male", "female"], value="male", label="Sex")
                            stt = gr.Slider(0, 1, 0, step=0.05, label="ST-T drift (ST-T segment only)")
                            seed = gr.Slider(0, 50, 1, step=1, label="Random seed")
                            go = gr.Button("Run frozen clocks", variant="primary")
                        with gr.Column(scale=2):
                            out_md = gr.Markdown()
                    with gr.Row():
                        f_fp = gr.Plot(label="Fingerprint")
                        f_beat = gr.Plot(label="Median beat")
                        f_geo = gr.Plot(label="A–D geometry")
                    go.click(run_synth, [hr, age, sex, stt, seed],
                             [out_md, f_fp, f_beat, f_geo])
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
