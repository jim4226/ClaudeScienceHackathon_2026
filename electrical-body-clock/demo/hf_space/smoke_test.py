#!/usr/bin/env python3
"""Headless smoke test for the HeartVector demo Space (`make demo-smoke`).

Loads the frozen clocks, scores a bundled real PTB-XL example end-to-end, checks
input validation, and builds the Gradio app object — WITHOUT launching a server.
Exit 0 iff everything works.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)


def main() -> int:
    import json
    import app, inference as inf

    labels = app._example_labels()
    assert labels, "no bundled examples found"

    # 1. score every bundled real example through the frozen harness
    for lab in labels:
        md, fp, beat, geo = app.run_example(lab, 0, "male")
        assert fp is not None and beat is not None and geo is not None, f"plots failed for {lab}"
        assert "PTB-XL" in md, f"example readout missing attribution for {lab}"
    print(f"[ok] scored {len(labels)} real PTB-XL examples")

    # 2. synthetic path builds + is labeled an interface illustration
    md, fp, _, _ = app.run_synth(70, 55, "male", 0.3, 1)
    assert fp is not None and "Interface illustration" in md
    print("[ok] synthetic interface-illustration path")

    # 3. input validation guards fire
    import numpy as np, tempfile
    uv = inf.synth_12lead(70, seed=2) * 1000.0     # microvolt-scale -> must reject
    p = tempfile.mktemp(suffix=".csv"); np.savetxt(p, uv, delimiter=",")
    try:
        inf.parse_uploaded(p); print("[FAIL] microvolt guard did not fire"); return 1
    except ValueError:
        print("[ok] CSV unit-scale validation")
    try:
        inf.parse_uploaded("/tmp/does_not_exist.hea"); print("[FAIL] missing-.dat guard"); return 1
    except ValueError:
        print("[ok] WFDB requires-.dat validation")

    # 4. UI builds
    assert app.build() is not None
    print("[ok] Gradio app builds")
    print("DEMO SMOKE: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
