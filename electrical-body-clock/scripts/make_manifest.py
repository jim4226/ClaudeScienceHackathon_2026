#!/usr/bin/env python3
"""Generate RELEASE_MANIFEST.sha256 for the electrical arm.

Hashes the release-critical, content-frozen files — demo weights, the frozen
scorer + fixture + protocol lock, the reveal receipt + script, released result
tables, figures, and the compiled PDFs — so a reviewer can verify byte-for-byte
integrity with `make verify` (or `sha256sum -c`). Paths in the manifest are
relative to electrical-body-clock/.
"""
from __future__ import annotations
import hashlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)

# directories whose files are all release-critical
DIRS = [
    "results",
    "demo/hf_space/hv_bundle/models",
    "demo/hf_space/examples",
    "paper/figs_full",
    "paper/figs_c2c",
]
# individual files
FILES = [
    "CLAIM_TO_ARTIFACT_LEDGER.md",
    "demo/hf_space/hv_bundle/hv_frozen.py",
    "demo/hf_space/hv_bundle/FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json",
    "demo/hf_space/inference.py",
    "demo/hf_space/app.py",
    "paper/from_clocks_to_coordinates_full.pdf",
    "paper/clocks_to_coordinates.pdf",
    "paper/manuscript.pdf",
]

# extensions worth hashing inside DIRS (skip caches, __pycache__, etc.)
KEEP = {".json", ".csv", ".parquet", ".md", ".py", ".pt", ".hea", ".dat",
        ".pdf", ".png"}


def iter_files():
    for d in DIRS:
        root = os.path.join(ARM, d)
        for dp, _, fns in os.walk(root):
            if "__pycache__" in dp:
                continue
            for fn in fns:
                if os.path.splitext(fn)[1].lower() in KEEP:
                    yield os.path.relpath(os.path.join(dp, fn), ARM)
    for f in FILES:
        if os.path.exists(os.path.join(ARM, f)):
            yield f


def main():
    rows = []
    for rel in sorted(set(iter_files())):
        h = hashlib.sha256(open(os.path.join(ARM, rel), "rb").read()).hexdigest()
        rows.append(f"{h}  {rel}")
    out = os.path.join(ARM, "RELEASE_MANIFEST.sha256")
    with open(out, "w") as fh:
        fh.write("# SHA-256 release manifest — electrical-body-clock/\n")
        fh.write("# regenerate: python scripts/make_manifest.py ; verify: make verify\n")
        fh.write("\n".join(rows) + "\n")
    print(f"wrote {out} ({len(rows)} files)")


if __name__ == "__main__":
    main()
