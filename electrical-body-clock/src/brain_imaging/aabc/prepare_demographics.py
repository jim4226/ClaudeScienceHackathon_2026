#!/usr/bin/env python3
"""
prepare_demographics.py — the ONE missing piece for the real AABC run.

The four predictor channels + Toolbox outcomes are in hand, but NONE of them
carry chronological age (the brain-age clock TARGET) or the primary-model
covariates. Those live in the BALSA non-imaging data export, e.g.
    AABC_Release2_Non-imaging_Data-XL.csv

This script validates that file has what the pipeline needs and writes a clean
`demographics.csv` keyed on id_event. Run it wherever the real analysis runs
(Modal recommended). It reads ONLY predictor-side variables (age + covariates) —
never the gait outcome — so it does not touch outcome-blinding.

Usage:
    python prepare_demographics.py --nonimaging AABC_Release2_Non-imaging_Data-XL.csv \
                                   --out demographics.csv
"""
import argparse, sys, re
import pandas as pd

# what the pipeline needs, and the aliases BALSA exports sometimes use
NEEDED = {
    "id_event":      ["id_event", "x___", "subject_visit", "id_visit"],
    "age_open":      ["age_open", "age", "interview_age", "age_at_visit", "chronological_age"],
    "sex":           ["sex", "gender", "sex_at_birth"],
    "site":          ["site", "scanner_site", "acquisition_site"],
    "education":     ["education", "educ", "years_education", "edu_years"],
    "height_inches": ["height_inches", "height_in", "height"],
    "bmi":           ["bmi", "body_mass_index"],
    "days_from_V1":  ["days_from_v1", "days_from_baseline", "visit_days", "days_since_v1"],
}
REQUIRED = ["id_event", "age_open"]   # clocks cannot train without these two
OPTIONAL = [k for k in NEEDED if k not in REQUIRED]  # covariate-adjustment; degrade gracefully


def find_col(df_cols, aliases):
    low = {c.lower().strip(): c for c in df_cols}
    for a in aliases:
        if a.lower() in low:
            return low[a.lower()]
    # loose contains-match as a fallback
    for a in aliases:
        for lc, orig in low.items():
            if a.lower() in lc:
                return orig
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonimaging", required=True, help="BALSA non-imaging data CSV")
    ap.add_argument("--out", default="demographics.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.nonimaging, encoding="latin-1", low_memory=False)
    print(f"loaded {args.nonimaging}: {df.shape[0]} rows x {df.shape[1]} cols")

    mapping, missing = {}, []
    for canon, aliases in NEEDED.items():
        col = find_col(df.columns, aliases)
        if col:
            mapping[canon] = col
        elif canon in REQUIRED:
            missing.append(canon)
    if missing:
        sys.exit(f"FATAL: required column(s) not found: {missing}\n"
                 f"  available columns (first 40): {list(df.columns)[:40]}")

    out = pd.DataFrame({canon: df[src] for canon, src in mapping.items()})
    # derive id / event from id_event if not separately present
    out["id"]    = out["id_event"].astype(str).str.replace(r"_(V\d+)$", "", regex=True)
    out["event"] = out["id_event"].astype(str).str.extract(r"_(V\d+)$")[0].fillna("V1")
    # fill absent optional covariates with NaN so the pipeline can decide how to handle
    for canon in OPTIONAL:
        if canon not in out.columns:
            out[canon] = pd.NA
            print(f"  NOTE: optional covariate '{canon}' not found — primary model will "
                  f"drop it (report the reduced adjustment set).")
    out.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}: {out.shape[0]} rows")
    print(f"  age_open present for {out['age_open'].notna().sum()} rows "
          f"(range {out['age_open'].min():.0f}-{out['age_open'].max():.0f})")
    cov_have = [c for c in OPTIONAL if out[c].notna().any()]
    print(f"  covariates available: {cov_have}")
    print("\nOK — hand this demographics.csv to run_pipeline.py.")


if __name__ == "__main__":
    main()
