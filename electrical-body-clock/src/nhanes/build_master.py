#!/usr/bin/env python
"""
build_master.py — assemble the NHANES 2005-2010 master analysis table (Act II).

Pools the DEMO / biomarker / questionnaire XPT modules across cycles D, E, F,
parses the fixed-width NCHS linked-mortality files, averages the up-to-three
blood-pressure readings, and computes derived columns:
  * eGFR   — CKD-EPI 2021 race-free equation from serum creatinine
  * NLR    — neutrophil-to-lymphocyte ratio
  * PP     — pulse pressure (SBP - DBP)

Input : data/nhanes/{MODULE}_{D,E,F}.xpt, data/nhanes/MORT_{D,E,F}.dat
Output: data/nhanes/master.parquet
"""
import os
import numpy as np
import pandas as pd

NH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "nhanes")
NH = os.path.abspath(NH)
CYC = ["D", "E", "F"]

# Columns to keep from each module
KEEP = {
    "DEMO":   ["RIDAGEYR", "RIAGENDR", "RIDRETH1", "INDFMPIR", "WTMEC2YR", "SDMVPSU", "SDMVSTRA"],
    "BIOPRO": ["LBXSAL", "LBXSATSI", "LBXSASSI", "LBXSAPSI", "LBXSBU", "LBXSCR",
               "LBXSGTSI", "LBXSGL", "LBXSTB", "LBXSTP", "LBXSUA", "LBXSGB", "LBXSC3SI"],
    "CBC":    ["LBXWBCSI", "LBXLYPCT", "LBXNEPCT", "LBXMOPCT", "LBDLYMNO", "LBDNENO",
               "LBXRBCSI", "LBXHGB", "LBXHCT", "LBXMCVSI", "LBXRDW", "LBXPLTSI", "LBXMPSI"],
    "CRP":    ["LBXCRP"],
    "GHB":    ["LBXGH"],
    "TCHOL":  ["LBXTC"],
    "HDL":    ["LBDHDD"],
    "TRIGLY": ["LBXTR", "LBDLDL"],
    "BPX":    ["BPXSY1", "BPXSY2", "BPXSY3", "BPXDI1", "BPXDI2", "BPXDI3", "BPXPLS"],
    "BMX":    ["BMXBMI", "BMXWAIST"],
    "MCQ":    ["MCQ160B", "MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F", "MCQ160L",
               "MCQ220", "MCQ160K", "MCQ160G", "MCQ160A"],
    "DIQ":    ["DIQ010", "DIQ050", "DIQ070"],
    "BPQ":    ["BPQ020", "BPQ040A", "BPQ080", "BPQ090D", "BPQ050A", "BPQ100D"],
    "KIQ_U":  ["KIQ022"],
    "SMQ":    ["SMQ020", "SMQ040"],
    "ALQ":    ["ALQ130", "ALQ120Q"],
}

# NCHS linked-mortality fixed-width layout (2019 public-use release)
MORT_COLSPECS = [("SEQN", 0, 6), ("ELIGSTAT", 14, 15), ("MORTSTAT", 15, 16),
                 ("UCOD_LEADING", 16, 19), ("DIABETES", 19, 20), ("HYPERTEN", 20, 21),
                 ("PERMTH_INT", 42, 45), ("PERMTH_EXM", 45, 48)]


def read_xpt(path):
    return pd.read_sas(path, format="xport")


def pool(stem, cols):
    """Read stem_D/E/F, keep SEQN + requested cols, concat across cycles."""
    parts = []
    for L in CYC:
        df = read_xpt(os.path.join(NH, f"{stem}_{L}.xpt"))
        df["SEQN"] = df["SEQN"].astype("int64")
        keep = ["SEQN"] + [c for c in cols if c in df.columns]
        parts.append(df[keep])
    return pd.concat(parts, ignore_index=True)


def egfr_ckdepi(scr, age, sex):
    """CKD-EPI 2021 race-free eGFR from serum creatinine (mg/dL). sex: 1=M, 2=F."""
    scr = np.asarray(scr, float); age = np.asarray(age, float)
    female = (np.asarray(sex) == 2)
    kappa = np.where(female, 0.7, 0.9)
    alpha = np.where(female, -0.241, -0.302)
    r = scr / kappa
    return (142 * np.minimum(r, 1) ** alpha * np.maximum(r, 1) ** (-1.200)
            * 0.9938 ** age * np.where(female, 1.012, 1.0))


def main():
    names = [c[0] for c in MORT_COLSPECS]
    colspecs = [(c[1], c[2]) for c in MORT_COLSPECS]
    mort = pd.concat(
        [pd.read_fwf(os.path.join(NH, f"MORT_{L}.dat"), colspecs=colspecs, names=names,
                     na_values=[".", ""], dtype={"SEQN": "Int64"}) for L in CYC],
        ignore_index=True)
    mort["SEQN"] = mort["SEQN"].astype("int64")

    master = pool("DEMO", KEEP["DEMO"])
    for stem in [s for s in KEEP if s != "DEMO"]:
        master = master.merge(pool(stem, KEEP[stem]), on="SEQN", how="left")
    master = master.merge(mort, on="SEQN", how="left")

    # Average up-to-3 BP readings
    master["SBP"] = master[["BPXSY1", "BPXSY2", "BPXSY3"]].mean(axis=1)
    master["DBP"] = master[["BPXDI1", "BPXDI2", "BPXDI3"]].mean(axis=1)
    # Derived columns
    master["eGFR"] = egfr_ckdepi(master["LBXSCR"], master["RIDAGEYR"], master["RIAGENDR"])
    master["NLR"] = master["LBDNENO"] / master["LBDLYMNO"].replace(0, np.nan)
    master["PP"] = master["SBP"] - master["DBP"]

    out = os.path.join(NH, "master.parquet")
    master.to_parquet(out)
    print(f"master: {master.shape} -> {out}")
    print(f"adults 20-79: {((master.RIDAGEYR >= 20) & (master.RIDAGEYR < 80)).sum()}")
    print(f"mortality-eligible: {(master.ELIGSTAT == 1).sum()}  deaths: {(master.MORTSTAT == 1).sum()}")


if __name__ == "__main__":
    main()
