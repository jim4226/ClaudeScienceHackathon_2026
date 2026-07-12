#!/usr/bin/env python
"""
nhanes_organ_clocks.py — Act II: six organ-system age clocks + mortality analysis.

Pipeline (reads data/nhanes/master.parquet from build_master.py):
  1. Train an elastic-net chronological-age predictor per organ system in
     disease-/medication-free healthy adults; read out a bias-corrected age-gap.
     Total cholesterol and eGFR are EXCLUDED as principled confounds (cholesterol
     paradox; eGFR is computed from age via CKD-EPI -> circular).
  2. Per-organ Cox (age+sex-adjusted) and a mutually-adjusted joint Cox for
     all-cause mortality; Benjamini-Hochberg FDR.
  3. Added-value C-index ladder via leak-free out-of-fold (5-fold) Cox, with a
     paired bootstrap on the out-of-fold predictions and a likelihood-ratio test.
  4. Smoking dose-response (never/former/current) of each organ-age gap.

Outputs -> results/act2_nhanes/
  organ_gaps.parquet, surv.parquet, clock_stats.json,
  nhanes_clock_performance.csv, nhanes_cox_results.csv,
  nhanes_smoking_attribution.csv, ladder.json
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.metrics import r2_score, mean_absolute_error
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from lifelines.statistics import proportional_hazard_test
from statsmodels.stats.multitest import multipletests
from scipy import stats
from scipy.stats import chi2

HERE = os.path.dirname(__file__)
NH = os.path.abspath(os.path.join(HERE, "..", "..", "data", "nhanes"))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "results", "act2_nhanes"))
os.makedirs(OUT, exist_ok=True)

ORGAN_NAMES = ["Cardiovascular", "Metabolic", "Renal", "Hepatic", "Immune", "Hematologic"]

# Canonical age-clock panels: total cholesterol dropped from Cardiovascular
# (non-monotonic with age); eGFR dropped from Renal (age-derived via CKD-EPI).
ORGANS = {
    "Cardiovascular": ["SBP", "DBP", "PP", "BPXPLS"],
    "Metabolic":      ["LBXGH", "BMXBMI", "BMXWAIST", "LBXSGL"],
    "Renal":          ["LBXSCR", "LBXSBU", "LBXSAL", "LBXSUA"],
    "Hepatic":        ["LBXSATSI", "LBXSASSI", "LBXSGTSI", "LBXSAPSI", "LBXSTB", "LBXSTP", "LBXSGB"],
    "Immune":         ["LBXCRP", "LBXWBCSI", "LBDNENO", "LBDLYMNO", "LBXMOPCT", "NLR"],
    "Hematologic":    ["LBXRBCSI", "LBXHGB", "LBXHCT", "LBXMCVSI", "LBXRDW", "LBXPLTSI", "LBXMPSI"],
}
LOG_MARKERS = {"LBXSATSI", "LBXSASSI", "LBXSGTSI", "LBXSAPSI", "LBXCRP", "NLR", "LBXSTB", "LBXSGL", "LBXSUA"}


def build_clock(A, global_healthy, organ_biochem, name, feats):
    """Elastic-net age clock in healthy adults; return per-participant bias-corrected gap."""
    X = A[feats].copy()
    for c in feats:
        if c in LOG_MARKERS:
            X[c] = np.log1p(X[c].clip(lower=0))
    cohort = X.notna().all(axis=1)
    healthy = cohort & global_healthy & organ_biochem[name]
    Xc = X[cohort]; agec = A.loc[cohort, "RIDAGEYR"].values
    Xh = X[healthy]; ageh = A.loc[healthy, "RIDAGEYR"].values
    sc = StandardScaler().fit(Xh)
    en = ElasticNetCV(l1_ratio=[.1, .5, .7, .9, .99], cv=5, max_iter=5000,
                      n_jobs=-1, random_state=0).fit(sc.transform(Xh), ageh)
    cvpred = cross_val_predict(
        ElasticNetCV(l1_ratio=[.1, .5, .7, .9, .99], cv=5, max_iter=5000, random_state=0),
        sc.transform(Xh), ageh, cv=KFold(5, shuffle=True, random_state=1), n_jobs=-1)
    r2 = r2_score(ageh, cvpred); mae = mean_absolute_error(ageh, cvpred)
    pred = en.predict(sc.transform(Xc)); raw = pred - agec
    hh = healthy[cohort].values
    b, a0 = np.polyfit(agec[hh], raw[hh], 1)      # bias-correct: fit gap~age on healthy
    corr = raw - (a0 + b * agec)
    out = pd.DataFrame({"SEQN": A.loc[cohort, "SEQN"].values, f"gap_{name}": corr})
    return out, dict(n_cohort=int(cohort.sum()), n_healthy=int(healthy.sum()),
                     cv_r2=round(r2, 3), cv_mae=round(mae, 2), n_feats=len(feats))


def main():
    master = pd.read_parquet(os.path.join(NH, "master.parquet"))
    A = master[(master.RIDAGEYR >= 20) & (master.RIDAGEYR < 80)].copy()

    # Disease-/medication-free reference for clock training
    global_healthy = (
        A["MCQ160B"].ne(1) & A["MCQ160C"].ne(1) & A["MCQ160E"].ne(1) & A["MCQ160F"].ne(1) &
        A["DIQ010"].ne(1) & A["DIQ070"].ne(1) & A["DIQ050"].ne(1) &
        A["MCQ220"].ne(1) & A["KIQ022"].ne(1) & A["MCQ160L"].ne(1) &
        A["BPQ050A"].ne(1) & A["BPQ100D"].ne(1))
    organ_biochem = {
        "Cardiovascular": (A["SBP"] < 140) & (A["DBP"] < 90),
        "Metabolic":      (A["LBXGH"] < 6.5),
        "Renal":          (A["eGFR"] >= 60),
        "Hepatic":        (A["LBXSATSI"] < 120) & (A["LBXSASSI"] < 120),
        "Immune":         (A["LBXCRP"] < 10),
        "Hematologic":    ((A["RIAGENDR"] == 1) & (A["LBXHGB"] >= 13)) |
                          ((A["RIAGENDR"] == 2) & (A["LBXHGB"] >= 12)),
    }

    gaps = A[["SEQN"]].copy(); clock_stats = {}
    for name, feats in ORGANS.items():
        out, st = build_clock(A, global_healthy, organ_biochem, name, feats)
        gaps = gaps.merge(out, on="SEQN", how="left"); clock_stats[name] = st
        print(f"{name:15s} n_cohort={st['n_cohort']:5d} CV_R2={st['cv_r2']:.3f} MAE={st['cv_mae']:.1f}yr")
    gaps.to_parquet(os.path.join(OUT, "organ_gaps.parquet"))
    json.dump(clock_stats, open(os.path.join(OUT, "clock_stats.json"), "w"), indent=1)
    pd.DataFrame([{"organ": k, "n_train_healthy": v["n_healthy"], "n_cohort": v["n_cohort"],
                   "cv_r2": v["cv_r2"], "cv_mae_yr": v["cv_mae"], "n_features": v["n_feats"]}
                  for k, v in clock_stats.items()]).to_csv(
                      os.path.join(OUT, "nhanes_clock_performance.csv"), index=False)

    # ---- Survival frame ----
    gapcols = [f"gap_{o}" for o in ORGAN_NAMES]
    surv = master[["SEQN", "RIDAGEYR", "RIAGENDR", "ELIGSTAT", "MORTSTAT",
                   "PERMTH_EXM", "PERMTH_INT"]].merge(gaps, on="SEQN", how="inner")
    surv = surv[surv.ELIGSTAT == 1].copy()
    surv["time_yr"] = surv["PERMTH_EXM"].fillna(surv["PERMTH_INT"]) / 12.0
    surv["event"] = (surv["MORTSTAT"] == 1).astype(int)
    surv["female"] = (surv["RIAGENDR"] == 2).astype(int)
    surv["age"] = surv["RIDAGEYR"]
    surv = surv[(surv.time_yr > 0) & surv.time_yr.notna()]
    for c in gapcols:
        surv[c + "_z"] = (surv[c] - surv[c].mean()) / surv[c].std()
    surv.to_parquet(os.path.join(OUT, "surv.parquet"))
    print(f"\nAnalytic cohort n={len(surv)}, deaths={int(surv.event.sum())}, "
          f"median FU {surv.time_yr.median():.1f} yr, {surv.time_yr.sum():,.0f} person-years")

    # ---- Per-organ Cox (age+sex-adjusted) ----
    rows = []
    for o in ORGAN_NAMES:
        z = f"gap_{o}_z"
        d = surv[["time_yr", "event", z, "age", "female"]].dropna()
        cph = CoxPHFitter().fit(d, "time_yr", "event")
        hr = np.exp(cph.params_[z]); ci = np.exp(cph.confidence_intervals_.loc[z].values)
        rows.append(dict(organ=o, n=len(d), events=int(d.event.sum()),
                         HR_adj_agesex=hr, lo_uni=ci[0], hi_uni=ci[1], p_uni=cph.summary.loc[z, "p"]))
    cox = pd.DataFrame(rows)
    cox["pfdr_uni"] = multipletests(cox["p_uni"], method="fdr_bh")[1]

    # ---- Mutually-adjusted joint Cox + PH check ----
    zcols = [f"gap_{o}_z" for o in ORGAN_NAMES]
    D = surv.dropna(subset=zcols + ["time_yr", "event", "age", "female"]).copy()
    cphj = CoxPHFitter().fit(D[["time_yr", "event", "age", "female"] + zcols], "time_yr", "event")
    joint = cphj.summary.loc[zcols, ["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]]
    joint.columns = ["HR_joint", "lo_joint", "hi_joint", "p_joint"]
    joint.index = ORGAN_NAMES
    cox = cox.merge(joint.reset_index().rename(columns={"index": "organ"}), on="organ")
    cox = cox.sort_values("HR_adj_agesex", ascending=False).reset_index(drop=True)
    cox.to_csv(os.path.join(OUT, "nhanes_cox_results.csv"), index=False)
    zph = proportional_hazard_test(cphj, D[["time_yr", "event", "age", "female"] + zcols],
                                   time_transform="rank")
    print("\nPer-organ Cox (HR per +1 SD gap):")
    print(cox[["organ", "HR_adj_agesex", "lo_uni", "hi_uni", "pfdr_uni", "HR_joint", "p_joint"]].round(3).to_string(index=False))
    print(f"\nPH global test min p = {zph.summary['p'].min():.3f} (all should exceed ~0.05)")

    # ---- C-index ladder: leak-free out-of-fold Cox ----
    kf = KFold(5, shuffle=True, random_state=42)
    ladder_feats = {
        "Age only": ["age"],
        "Age + sex": ["age", "female"],
        "Age + sex + 1 system (best: Hepatic)": ["age", "female", "gap_Hepatic_z"],
        "Age + sex + all 6 systems": ["age", "female"] + zcols,
    }
    oof = {name: np.zeros(len(D)) for name in ladder_feats}
    Dr = D.reset_index(drop=True)
    for tr, te in kf.split(Dr):
        for name, feats in ladder_feats.items():
            cph = CoxPHFitter(penalizer=0.01).fit(
                Dr.iloc[tr][["time_yr", "event"] + feats], "time_yr", "event")
            oof[name][te] = np.log(cph.predict_partial_hazard(Dr.iloc[te][feats]).values)
    t, e = Dr["time_yr"].values, Dr["event"].values
    cidx = {name: concordance_index(t, -oof[name], e) for name in ladder_feats}

    # paired bootstrap on OOF predictions (full vs age+sex)
    rng = np.random.default_rng(7); n = len(Dr); deltas = []
    base, full = oof["Age + sex"], oof["Age + sex + all 6 systems"]
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        deltas.append(concordance_index(t[idx], -full[idx], e[idx]) -
                      concordance_index(t[idx], -base[idx], e[idx]))
    deltas = np.array(deltas); dlo, dhi = np.percentile(deltas, [2.5, 97.5])

    # likelihood-ratio test
    llb = CoxPHFitter().fit(D[["time_yr", "event", "age", "female"]], "time_yr", "event").log_likelihood_
    llf = cphj.log_likelihood_
    lr = 2 * (llf - llb); plr = chi2.sf(lr, len(zcols))

    ladder = dict(cindex={k: round(float(v), 4) for k, v in cidx.items()},
                  n=int(len(D)), deaths=int(D.event.sum()),
                  delta_c=round(float(cidx["Age + sex + all 6 systems"] - cidx["Age + sex"]), 4),
                  delta_lo=round(float(dlo), 4), delta_hi=round(float(dhi), 4),
                  boot_p_gt0=float((deltas > 0).mean()),
                  lr_chi2=round(float(lr), 1), lr_df=len(zcols), lr_p=float(plr))
    json.dump(ladder, open(os.path.join(OUT, "ladder.json"), "w"), indent=1)
    print("\nC-index ladder:", {k: round(v, 3) for k, v in cidx.items()})
    print(f"delta-C = +{ladder['delta_c']:.4f} (95% CI {dlo:.4f}-{dhi:.4f}), "
          f"LR chi2({len(zcols)})={lr:.0f} p={plr:.1e}")

    # ---- Smoking dose-response ----
    sm = master[["SEQN", "SMQ020", "SMQ040"]].merge(gaps, on="SEQN", how="inner")

    def status(r):
        if r.SMQ020 == 2: return "Never"
        if r.SMQ020 == 1 and r.SMQ040 == 3: return "Former"
        if r.SMQ020 == 1 and r.SMQ040 in (1, 2): return "Current"
        return None
    sm["smoke"] = sm.apply(status, axis=1)
    sm = sm[sm.smoke.isin(["Never", "Former", "Current"])]
    srows = []
    for o in ORGAN_NAMES:
        g = f"gap_{o}"
        means = {s: sm.loc[sm.smoke == s, g].mean() for s in ["Never", "Former", "Current"]}
        nev = sm.loc[sm.smoke == "Never", g].dropna(); cur = sm.loc[sm.smoke == "Current", g].dropna()
        _, p = stats.ttest_ind(cur, nev, equal_var=False)
        d = (cur.mean() - nev.mean()) / np.sqrt((cur.var() + nev.var()) / 2)
        srows.append(dict(organ=o, Never=means["Never"], Former=means["Former"],
                          Current=means["Current"], delta=cur.mean() - nev.mean(), d=d, p=p))
    smoke = pd.DataFrame(srows)
    smoke["p_fdr"] = multipletests(smoke["p"], method="fdr_bh")[1]
    smoke = smoke.sort_values("delta", ascending=False).reset_index(drop=True)
    smoke.to_csv(os.path.join(OUT, "nhanes_smoking_attribution.csv"), index=False)
    print("\nSmoking dose-response (Current-minus-Never, years):")
    print(smoke[["organ", "Never", "Former", "Current", "delta", "p_fdr"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
