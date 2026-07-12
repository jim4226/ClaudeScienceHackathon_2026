#!/usr/bin/env python3
"""
Generate a small DEMO canonical-TSV so run.sh works offline with zero data
downloads. In a real run this file is PRODUCED BY P1/P2 (zooHARs + liftOver +
phyloP + gBGC), not by this script. Columns match the canonical schema exactly.

The demo includes the frozen controls (GDF5-GROW1, GDF5-R4, HACNS1, negatives)
at their real hg38 coordinates so the BLIND validation in aggregate.py exercises
real rows. All engine-score columns are left blank (NaN) — the scoring modules
fill them.
"""
from __future__ import annotations
import argparse
import numpy as np
import pandas as pd

CANONICAL_COLUMNS = [
    "har_id", "chrom", "pos_hg38", "ref_ancestral", "alt_human",
    "target_gene_hypothesis",
    "phylop_241", "constrained", "rocc",
    "gbgc_class", "recomb_rate_cMperMb", "gbgc_flag",
    "ag_atac_delta", "ag_dnase_delta",
    "cbp_limb_logfc", "cbp_msc_logfc", "cbp_mg63_logfc", "cbp_jsd",
    "neural_delta",
    "skeletal_specific",
    "candidate",
    "oa_credible_overlap", "oa_credible_set_id", "gwas_enrich_p",
    "composite_score", "empirical_p", "fdr_bh",
    "is_control", "notes",
]

# (har_id, chrom, pos_hg38, ref, alt, gene, is_control)
CONTROLS = [
    ("GDF5-GROW1", "chr20", 35364817, "A", "G", "GDF5", "GDF5-GROW1"),   # rs4911178
    ("GDF5-R4",    "chr20", 35319358, "C", "T", "GDF5", "GDF5-R4"),      # rs6060369
    ("HACNS1",     "chr2",  236254000, "G", "A", "GBX2", "HACNS1"),      # TODO(verify): confirm HACNS1/2xHAR3 hg38 coord + alleles
    ("NEG-1",      "chr1",  1000000,   "A", "T", "NA",   "negative"),
    ("NEG-2",      "chr7",  5000000,   "C", "G", "NA",   "negative"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-random", type=int, default=60, help="random non-control HARs")
    args = ap.parse_args()

    rng = np.random.default_rng(7)
    rows = []
    for (hid, chrom, pos, ref, alt, gene, ctrl) in CONTROLS:
        rows.append(dict(har_id=hid, chrom=chrom, pos_hg38=pos, ref_ancestral=ref,
                         alt_human=alt, target_gene_hypothesis=gene, is_control=ctrl))
    bases = list("ACGT")
    for i in range(args.n_random):
        c = f"chr{rng.integers(1, 22)}"
        ref, alt = rng.choice(bases, size=2, replace=False)
        rows.append(dict(har_id=f"zooHAR_{i:04d}", chrom=c,
                         pos_hg38=int(rng.integers(1_000_000, 200_000_000)),
                         ref_ancestral=ref, alt_human=alt,
                         target_gene_hypothesis="NA", is_control="none"))

    df = pd.DataFrame(rows)
    # Fill P2-provided columns with plausible demo values so the matched null runs.
    df["phylop_241"] = np.round(rng.normal(1.0, 1.8, len(df)), 3)
    df["constrained"] = df["phylop_241"] > 2.27
    df["rocc"] = rng.random(len(df)) < 0.15
    classes = rng.choice(["WtoS", "StoW", "neutral"], size=len(df), p=[0.3, 0.3, 0.4])
    df["gbgc_class"] = classes
    df["recomb_rate_cMperMb"] = np.round(np.abs(rng.normal(1.2, 1.5, len(df))), 3)
    df["gbgc_flag"] = (df["gbgc_class"] == "WtoS") & (df["recomb_rate_cMperMb"] > 2.0)

    # Engine + downstream columns start empty.
    for c in CANONICAL_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df["oa_credible_overlap"] = False
    df["oa_credible_set_id"] = ""
    df["notes"] = ""

    df = df[CANONICAL_COLUMNS]
    df.to_csv(args.out, sep="\t", index=False)
    print(f"wrote demo input {args.out} ({len(df)} rows, {len(CONTROLS)} controls)")


if __name__ == "__main__":
    main()
