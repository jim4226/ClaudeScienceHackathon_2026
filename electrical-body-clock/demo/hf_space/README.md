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
   - *Synthesize an ECG* — build a physiologically-plausible synthetic 12-lead
     ECG (no patient data) with adjustable heart rate / morphology, then score it
     live. Returns the subsystem age-gap fingerprint, the median beat with the
     four subsystem windows highlighted, and the record's position in the A–D plane.
   - *Upload your own* — a WFDB record (`.hea` + `.dat`) or a 12-column CSV
     (canonical lead order I, II, III, aVR, aVL, aVF, V1–V6; samples in rows).
2. **Result explorer** — the frozen result figures: the perturbation compass,
   external Chapman transport, the multiscale organ atlas, brain-MRI disagreement,
   and the MotionVector structure–function boundary test.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

The app is self-contained: model weights, frozen definitions, and result figures
all ship inside this folder.

---
*Research demonstration only. Not a medical device; not for clinical or diagnostic use.*
