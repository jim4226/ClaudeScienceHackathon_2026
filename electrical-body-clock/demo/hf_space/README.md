---
title: HeartVector — From Clocks to Coordinates
emoji: 🫀
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 6.20.0
app_file: app.py
pinned: false
license: mit
short_description: Live 12-lead ECG to subsystem phase-age clocks and A/D geometry
---

# HeartVector — live demo

Jaron Mohammed · University of Miami · 2026 · MIT license ·
[github.com/jim4226/ClaudeScienceHackathon_2026](https://github.com/jim4226/ClaudeScienceHackathon_2026)

A deployable Gradio app for **From Clocks to Coordinates**. It runs the five
*frozen* subsystem phase-age clocks (whole-ECG, P, AV, QRS, ST-T) on a 12-lead
ECG, on CPU, and reads out the two coordinates the paper is about:

- **A** — the shared aging axis (how old the ECG looks overall), and
- **D** — the disagreement radius (how much the subsystem clocks disagree).

Everything is frozen from the manuscript: the five checkpoints in
`hv_bundle/models/` and every standardization constant in
`hv_bundle/FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json`. Nothing is refit at runtime.

## Tabs

1. **Live inference**
   - *Real example ECGs* (default) — score one of three **real 12-lead PTB-XL
     records** (CC-BY 4.0; ages 22, 52, 77; attributed in
     `examples/ATTRIBUTION.md`), each using its own recorded age and sex. Returns
     the signed subsystem age-gap fingerprint (a diverging bar chart, not a radar),
     the median beat with the four subsystem windows highlighted, and the record's
     position in the frozen calibration reference frame.
   - *Upload your own* — select **exactly one** 12-column CSV, or **exactly two**
     matching WFDB files (`record.hea` + `record.dat`). WFDB leads are reordered
     to canonical order from the header `sig_name`; CSV columns must use canonical
     lead order I, II, III, aVR, aVL, aVF, V1–V6, with samples in rows and
     amplitudes in millivolts. The validator rejects unexpected or mixed files,
     mismatched WFDB names or references, unsafe filenames, non-12-lead inputs,
     invalid sampling rates, short or over-5-minute records, non-finite values,
     implausible units, and files over the published size limits.
   - *Synthetic (interface illustration)* — a synthetic trace to exercise the
     controls without a record. It is **clearly labeled not a biological result**:
     the clocks run on out-of-distribution input, so the ages shown are interface
     artefacts. The ST-T drift control perturbs **only** the ST-T segment.
2. **Result explorer** — the frozen result figures: the perturbation compass,
   external Chapman transport, the multiscale organ atlas, brain-MRI disagreement,
   and the MotionVector structure–function boundary test.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

`requirements.txt` retains lower bounds for hosted-platform compatibility.
`requirements-lock.txt` records the exact environment used for the judged CPU
smoke test.

The app is self-contained: model weights, frozen definitions, and result figures
all ship inside this folder.

## Privacy and upload handling

**Do not upload identifiable, private, restricted, or protected health data.**
Prefer the bundled, explicitly licensed PTB-XL examples or synthetic interface
mode. If you use the upload tab, you are responsible for confirming that you are
authorized to process the record in the hosted environment.

The application reads a validated upload in the running Space, computes the
displayed result, and does not write the signal contents to an application
database or results store. Its short-lived validated WFDB working copy is deleted
immediately after parsing. The Gradio/Hugging Face hosting layer may still retain
temporary upload or cache files under the platform's own retention policy, so
this interface must not be treated as a private clinical-data vault.

---
*Research demonstration only. Not a medical device; not for clinical or diagnostic use.*
