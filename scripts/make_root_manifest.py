#!/usr/bin/env python3
"""Generate the ROOT-level RELEASE_MANIFEST.sha256 for the whole repository.

The per-arm manifest (electrical-body-clock/RELEASE_MANIFEST.sha256) seals the
electrical arm's frozen artifacts and both compiled PDFs. This root manifest
additionally seals the release-critical, content-frozen files that live OUTSIDE
that arm or that a reviewer specifically expects sealed at the top level:

  * both manuscript sources (.tex) + bibliographies (.bib) + the toolchain note,
  * the Skeletome real-pipeline result tables + the Borzoi scorer,
  * the root release docs (README, LICENSE, CITATION, DATA_LICENSES),
  * the build recipe (Makefile), and
  * the per-arm manifest file itself (so the root seal covers the arm seal).

Verify byte-for-byte with `make verify-root` (or `sha256sum -c` on the file).
Paths in the manifest are relative to the repository root.
"""
from __future__ import annotations
import hashlib, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Individual release-critical files, repo-root-relative.
FILES = [
    # root release docs
    "README.md",
    ".gitattributes",
    "LICENSE",
    "NOTICE.md",
    "CITATION.cff",
    "DATA_LICENSES.md",
    "SUBMISSION.md",
    "REPRODUCE.md",
    "HACKATHON_PROVENANCE.md",
    "CLAUDE_SCIENCE_METHODS.md",
    "Makefile",
    # manuscript source + bibliography + toolchain
    "electrical-body-clock/paper/from_clocks_to_coordinates_full.tex",
    "electrical-body-clock/paper/clocks_to_coordinates.tex",
    "electrical-body-clock/paper/manuscript.tex",
    "electrical-body-clock/paper/references.bib",
    "electrical-body-clock/paper/references_c2c.bib",
    "electrical-body-clock/paper/TOOLCHAIN.md",
    # compiled PDFs (headline deliverables)
    "electrical-body-clock/paper/from_clocks_to_coordinates_full.pdf",
    "electrical-body-clock/paper/clocks_to_coordinates.pdf",
    "electrical-body-clock/paper/manuscript.pdf",
    # Skeletome real-pipeline evidence (tables + scorer) behind the genomic figure
    "skeletome/results/borzoi_scores_full.csv",
    "skeletome/results/skeletome_top_candidates.csv",
    "skeletome/results/skeletome_triple_hits.csv",
    "skeletome/results/skeletome_pipeline_summary.json",
    "skeletome/results/skeletome_borzoi_track_indices.csv",
    "skeletome/claude_science_package/code/borzoi_score.py",
    # the per-arm manifest itself (root seal covers the arm seal)
    "electrical-body-clock/RELEASE_MANIFEST.sha256",
]


def main() -> None:
    rows = []
    missing = []
    for rel in sorted(set(FILES)):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            missing.append(rel)
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        rows.append(f"{h}  {rel}")
    out = os.path.join(ROOT, "RELEASE_MANIFEST.sha256")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# SHA-256 ROOT release manifest — repository-relative paths\n")
        fh.write("# seals manuscript .tex/.bib, Skeletome result tables + scorer,\n")
        fh.write("# root release docs, the build recipe, and the per-arm manifest.\n")
        fh.write("# regenerate: python scripts/make_root_manifest.py ; verify: make verify-root\n")
        fh.write("\n".join(rows) + "\n")
    print(f"wrote {out} ({len(rows)} files)")
    if missing:
        print("WARNING: missing (not hashed):")
        for m in missing:
            print(f"  {m}")


if __name__ == "__main__":
    main()
