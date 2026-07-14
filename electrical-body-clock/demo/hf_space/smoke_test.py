#!/usr/bin/env python3
"""Headless smoke test for the HeartVector demo Space (`make demo-smoke`).

Loads the frozen clocks, scores a bundled real PTB-XL example end-to-end, checks
input validation, and builds the Gradio app object — WITHOUT launching a server.
Exit 0 iff everything works.
"""
import os, sys
import shutil
import tempfile
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
    import numpy as np
    exdir = os.path.join(HERE, "examples")
    first = json.load(open(os.path.join(exdir, "examples_manifest.json")))[0]
    src_base = os.path.join(exdir, first["record"])
    with tempfile.TemporaryDirectory(prefix="heartvector_smoke_") as tmp:
        # Valid multi-file callback: the UI now truly accepts the required pair.
        hea = os.path.join(tmp, first["record"] + ".hea")
        dat = os.path.join(tmp, first["record"] + ".dat")
        shutil.copyfile(src_base + ".hea", hea)
        shutil.copyfile(src_base + ".dat", dat)
        sig, fs = inf.parse_uploaded_files([hea, dat])
        assert sig.shape[1] == 12 and fs == 500
        md, fp, beat, geo = app.run_upload(
            [hea, dat], float(first["age"]),
            "female" if first["sex"] == "F" else "male", 500)
        assert fp is not None and beat is not None and geo is not None
        assert "Frozen clocks" in md
        print("[ok] matching WFDB pair through upload callback")

        # A valid CSV passes shape/resource checks.
        csv_path = os.path.join(tmp, "valid.csv")
        np.savetxt(csv_path, inf.synth_12lead(70, seed=2), delimiter=",")
        sig_csv, fs_csv = inf.parse_uploaded_files([csv_path], csv_fs=500)
        assert sig_csv.shape == (5000, 12) and fs_csv == 500
        print("[ok] single 12-column CSV upload")

        # Microvolt-scale input is rejected after bounded structural validation.
        uv_path = os.path.join(tmp, "microvolts.csv")
        np.savetxt(uv_path, inf.synth_12lead(70, seed=3) * 1000.0, delimiter=",")
        try:
            inf.parse_uploaded_files([uv_path]); print("[FAIL] microvolt guard did not fire"); return 1
        except ValueError:
            print("[ok] CSV unit-scale validation")

        # Count/type/stem guards reject ambiguous or unexpected selections.
        bad_dat = os.path.join(tmp, "different.dat")
        shutil.copyfile(dat, bad_dat)
        for bad_files, label in (
            ([hea], "single WFDB file"),
            ([hea, bad_dat], "mismatched WFDB pair"),
            ([hea, csv_path], "mixed upload"),
            ([hea, dat, csv_path], "too many files"),
        ):
            try:
                inf.parse_uploaded_files(bad_files)
                print(f"[FAIL] {label} guard did not fire"); return 1
            except ValueError:
                pass
        print("[ok] upload count/type/stem validation")

        # A header cannot redirect the WFDB parser to another filesystem path.
        unsafe_hea = os.path.join(tmp, "unsafe.hea")
        unsafe_dat = os.path.join(tmp, "unsafe.dat")
        with open(hea, "r", encoding="utf-8") as handle:
            header_text = handle.read()
        header_text = header_text.replace(first["record"], "unsafe")
        header_text = header_text.replace("unsafe.dat", "../unsafe.dat")
        with open(unsafe_hea, "w", encoding="utf-8") as handle:
            handle.write(header_text)
        shutil.copyfile(dat, unsafe_dat)
        try:
            inf.parse_uploaded_files([unsafe_hea, unsafe_dat])
            print("[FAIL] WFDB path-reference guard did not fire"); return 1
        except ValueError:
            print("[ok] WFDB local-reference validation")

        short_csv = os.path.join(tmp, "short.csv")
        np.savetxt(short_csv, np.zeros((100, 12)), delimiter=",")
        try:
            inf.parse_uploaded_files([short_csv], csv_fs=500)
            print("[FAIL] short-record guard did not fire"); return 1
        except ValueError:
            print("[ok] CSV sample-count validation")

        oversized = os.path.join(tmp, "oversized.csv")
        with open(oversized, "wb") as handle:
            handle.truncate(inf.MAX_SIGNAL_FILE_BYTES + 1)
        try:
            inf.parse_uploaded_files([oversized])
            print("[FAIL] file-size guard did not fire"); return 1
        except ValueError:
            print("[ok] upload file-size validation")

    try:
        inf.parse_uploaded("/tmp/does_not_exist.hea"); print("[FAIL] missing-pair guard"); return 1
    except ValueError:
        print("[ok] WFDB requires both files")

    # 4. UI builds
    assert app.build() is not None
    print("[ok] Gradio app builds")
    print("DEMO SMOKE: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
