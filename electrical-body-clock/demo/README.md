# Interactive demo

## `electrical_body_clock_demo.html`
A self-contained (no server, no dependencies) walkthrough of the subsystem
electrical-age fingerprint. Open it in any browser. For a handful of held-out
PTB-XL patients it shows:

- the four subsystem age-gaps as a radar fingerprint,
- the patient's ECG with the four subsystem windows highlighted,
- a language-model reading that translates the four subsystem ages into a
  clinician-style interpretation and an explicit substrate-match verdict.

All images are inlined as base64, so the single `.html` file is the whole demo.

## `out_heart_saliency_viewer.html`
Grad-CAM / integrated-gradients saliency over the median beat for each
subsystem clock, showing which samples of the waveform each clock attends to.
Produced by [`src/analysis/heart_saliency.py`](../src/analysis/heart_saliency.py).

## `claude_extract_demo.json`
Worked examples of the language-model adjudicator used in the demo: each entry
pairs a PTB-XL cardiologist report (German + translation) with the model's
disease-group flags and the ground-truth `scp_codes` labels, illustrating how
the substrate-match verdict is formed.

---
*Research demonstration; not for clinical use.*
