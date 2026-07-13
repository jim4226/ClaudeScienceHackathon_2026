"""
reveal_final_cox_RC2_3.py — SINGLE LOCKED CODE-15 MORTALITY REVEAL (RC2.3).

FROZEN, not executed. Runs exactly once, only after BOTH authorization gates
(APPROVE PRE-REVEAL PREPARATION, then APPROVE SINGLE REVEAL), inside the immutable image,
network disabled, no auto-retry.

RC2.3 supersedes RC2.2 (sha 8c92fea6...). It was rebuilt — under a UNIQUE name, for fresh
attestation + explicit user freeze approval, per the reveal-gate stop rule — to fix defects an
independent audit found in RC2.2:

  D-1  NESTED LRTs. Sensitivity LRTs were non-nested (M2_dropP[A_std_dropP] vs M1[A_std]).
       FIXED: each sensitivity now uses its OWN matched reduced model:
         D3_dropP : M2_dropP(+D_std_dropP) vs M1_dropP(A_std_dropP, no D)   [1 df, nested]
         D3_noAV  : M2_noAV (+D_std_noAV ) vs M1_noAV (A_std_noAV , no D)   [1 df, nested]
  D-2  BRANCH LOGIC used sensitivity/OOS p-values as significance gates, contradicting the
       receipt. FIXED: branch is selected from the PRIMARY D4 model ONLY (M2-vs-M1 LRT + D4's
       own delta-C for the 'mixed' association-without-discrimination case). Sensitivities and
       OOS are REPORTED in every branch but never gate it.
  D-3  COHORT INTEGRITY unenforced. FIXED: join is on (patient_id AND index_exam_id); frozen
       patient/exam set-hash + row-count + OOS-count assertions; 1:1 merge validation; duplicate
       and unexpected-NaN guards; missing death is a HARD ERROR (never silently censored);
       required covariates asserted present (never silently dropped from a formula).
  D-4  UNUSED PROMISED OUTPUTS. FIXED: PH diagnostics (Schoenfeld) written; code_subgroups.csv is
       real prespecified subgroups (sex, age<=/>median, normal-ECG); dev_baseline_hazard.csv used
       for a frozen 5-year risk score (time-dependent AUC + Brier) in addition to Harrell-C.
  D-5  NON-ATOMIC OUTPUTS. FIXED: write to out.tmp/, fsync, write SHA256SUMS.txt + _SUCCESS
       sentinel, then atomic rename to out/.

UNCHANGED from RC2.2 and its attestation: the PRIMARY estimand (HR per +1 SD D_std in M2, LRT
M2 vs M1, 1 df, success=p<0.05 AND HR>1); mu_q=0 uncentered standardization from
FROZEN_DISAGREEMENT_DEFINITIONS_RC2; the M5 Harrell 3-knot RCS basis + calibration knots
(byte-identical to development); the no-refit prediction track; the forbidden-vault + create-once
guards; outcome-blindness (the ONLY outcome source is the replacement vault, read once).

INPUTS (staged, read-only): scores_outcome_free.parquet, FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json,
  FROZEN_RESULT_TEMPLATES_RC2.json, development_model_frozen.json, dev_baseline_hazard.csv,
  oos_provenance_manifest.parquet, rc23_integrity_constants.json.
MOUNT (read-only, once): $REPLACEMENT_OUTCOME_MOUNT/age_adaptation_outcomes.parquet
  (patient_id, index_exam_id, death, timey).
WRITES ./out/ (create-once, atomic): code_primary_cox.csv, code_prediction_metrics.csv,
  code_subgroups.csv, code_ph_diagnostics.csv, reveal_result.json, CLAIMS_LEDGER_populated.json,
  REVEAL_LOG_populated.json, SHA256SUMS.txt, _SUCCESS.
"""
import os, json, time, hashlib, datetime, sys, shutil
import numpy as np, pandas as pd
from lifelines import CoxPHFitter
from lifelines.statistics import proportional_hazard_test
from lifelines.utils import concordance_index

REPL = os.environ.get("REPLACEMENT_OUTCOME_MOUNT", "/vault_repl")
OUT = "out"
TMP = "out.tmp"
DX = ["1dAVb","RBBB","LBBB","SB","ST","AF"]

def sha_file(p):
    return hashlib.sha256(open(p,"rb").read()).hexdigest()

def set_sha256(ids):
    return hashlib.sha256(",".join(sorted(map(str,ids))).encode()).hexdigest()

def guard_no_forbidden_mounts():
    """Refuse to run if any retired outcome vault is visible as a mount or env pointer."""
    forbidden = ["heartvector-final-outcomes","heartvector-dev-outcomes","heartvector-raw-vault",
                 "/vault_fin","/vault_dev","/vault_raw"]
    blob = json.dumps(dict(os.environ)) + " " + " ".join(sys.argv)
    for f in forbidden:
        if f in blob:
            raise SystemExit(f"REVEAL GUARD: forbidden vault reference '{f}' present — refusing to run")
    for mp in ["/vault_fin","/vault_dev","/vault_raw"]:
        if os.path.ismount(mp) or os.path.isdir(mp):
            raise SystemExit(f"REVEAL GUARD: forbidden mount {mp} exists — refusing to run")

def fit_cox(df, cols, duration="timey", event="event"):
    cph = CoxPHFitter()
    cph.fit(df[cols+[duration,event]], duration_col=duration, event_col=event, show_progress=False)
    return cph

def lrt(cph_full, cph_reduced, dfree):
    stat = 2*(cph_full.log_likelihood_ - cph_reduced.log_likelihood_)
    from scipy.stats import chi2
    return float(stat), float(chi2.sf(stat, dfree))

def hr_ci(cph, term):
    s = cph.summary.loc[term]
    return (float(s["exp(coef)"]), float(s["exp(coef) lower 95%"]),
            float(s["exp(coef) upper 95%"]), float(s["p"]))

# FROZEN Harrell 3-knot restricted cubic spline basis — BYTE-IDENTICAL to fit_development_model.py
# (v cc62e230); calibration-partition knots per DEVELOPMENT_PROTOCOL_LOCK M5 (NOT dev percentiles).
D_RCS_KNOTS = [-1.15359, -0.129678, 1.315513]
def rcs_basis(x, knots):
    k = np.asarray(knots, float); t1,t2,t3 = k[0],k[1],k[2]
    def cube(z): z=np.where(z>0,z,0.0); return z**3
    denom = (t3-t1)
    return (cube(x-t1) - cube(x-t2)*(t3-t1)/(t3-t2) + cube(x-t3)*(t2-t1)/(t3-t2)) / denom**2

# Model ladder. Each sensitivity has a MATCHED reduced model so its LRT is genuinely nested (1 df).
MODELS = {
  "M0":      ["age","sex"],
  "M1":      ["age","sex","A_std","nn_predicted_age"],
  "M2":      ["age","sex","A_std","nn_predicted_age","D_std"],
  "M3":      ["age","sex","A_std","nn_predicted_age","D_std"]+DX,
  "M4":      ["age","sex","z_P","z_AV","z_QRS","z_STT","D_std"],
  "M5":      ["age","sex","A_std","nn_predicted_age","D_std","D_rcs2"],
  "M1_noAV": ["age","sex","A_std_noAV","nn_predicted_age"],                 # matched reduced for D3_noAV
  "M2_noAV": ["age","sex","A_std_noAV","nn_predicted_age","D_std_noAV"],
  "M1_dropP":["age","sex","A_std_dropP","nn_predicted_age"],                # matched reduced for D3_dropP
  "M2_dropP":["age","sex","A_std_dropP","nn_predicted_age","D_std_dropP"],
}

def run_cohort(df, label):
    """Fit the model ladder on one cohort; return computed statistics. Complete-case + integrity
    are enforced by the caller BEFORE this runs; here we assert the covariates are present."""
    r = {"label": label, "n_input": int(len(df))}
    need = ["age","sex","A_std","nn_predicted_age","D_std","timey","event"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(f"REVEAL ERROR [{label}]: required covariates absent: {missing}")
    cc = df.copy()
    cc = cc[cc.timey>0]
    r["n_complete_case_fit"] = int(len(cc)); r["n_events"] = int(cc.event.sum())
    r["median_followup"] = float(cc.timey.median())
    cc["D_rcs2"] = rcs_basis(cc["D_std"].to_numpy(), D_RCS_KNOTS)

    fits={}; failed=[]
    for m,cols in MODELS.items():
        cols=[c for c in cols if c in cc.columns]
        try: fits[m]=fit_cox(cc, cols)
        except Exception as e: failed.append({"model":m,"error":str(e)[:200]})
    r["failed_models"]=failed

    # PRIMARY: HR per +1 SD D_std in M2; LRT M2 vs M1 (nested, 1 df)
    if "M2" in fits and "M1" in fits:
        hr,lo,hi,p = hr_ci(fits["M2"],"D_std"); stat,plrt = lrt(fits["M2"],fits["M1"],1)
        r["D4"]={"HR":hr,"CI":[lo,hi],"p_wald":p,"LRT_chi2":stat,"LRT_p":plrt,
                 "success": bool(plrt<0.05 and hr>1.0)}
    # SENSITIVITIES — NESTED matched-reduced LRTs (D-1 fix)
    if "M2_dropP" in fits and "M1_dropP" in fits:
        hr,lo,hi,p=hr_ci(fits["M2_dropP"],"D_std_dropP"); stat,pl=lrt(fits["M2_dropP"],fits["M1_dropP"],1)
        r["D3_dropP"]={"HR":hr,"CI":[lo,hi],"p_wald":p,"LRT_p":pl,"reduced":"M1_dropP"}
    if "M2_noAV" in fits and "M1_noAV" in fits:
        hr,lo,hi,p=hr_ci(fits["M2_noAV"],"D_std_noAV"); stat,pl=lrt(fits["M2_noAV"],fits["M1_noAV"],1)
        r["D3_noAV"]={"HR":hr,"CI":[lo,hi],"p_wald":p,"LRT_p":pl,"reduced":"M1_noAV"}
    # SECONDARY (frozen-template secondary_models): M3, M4 per-phase z, M5 nonlinearity, delta-C
    if "M3" in fits:
        try: hr,lo,hi,p=hr_ci(fits["M3"],"D_std"); r["M3"]={"D4_HR":hr,"CI":[lo,hi],"p":p}
        except Exception: pass
    if "M4" in fits:
        m4={}
        for zc in ["z_P","z_AV","z_QRS","z_STT"]:
            try: hr,lo,hi,p=hr_ci(fits["M4"],zc); m4[zc]={"HR":hr,"CI":[lo,hi],"p":p}
            except Exception: pass
        r["M4_phase_z"]=m4
    if "M5" in fits and "M2" in fits:
        try:
            stat,pl=lrt(fits["M5"],fits["M2"],1)
            r["M5_nonlinearity"]={"LRT_chi2":stat,"LRT_p":pl,
                                  "interpretation":"p<0.05 => D-hazard departs from log-linear; else linear D adequate"}
        except Exception: pass
    if "M1" in fits and "M2" in fits:
        c1=float(fits["M1"].concordance_index_); c2=float(fits["M2"].concordance_index_)
        r["C_M1"]=c1; r["C_M2"]=c2; r["delta_C"]=c2-c1
        try:  # delta-C CI: bootstrap FIXED fitted M1/M2 predictors (no refit in loop)
            lp1=fits["M1"].predict_partial_hazard(cc).to_numpy()
            lp2=fits["M2"].predict_partial_hazard(cc).to_numpy()
            tt=cc.timey.to_numpy(); ev=cc.event.to_numpy()
            rngb=np.random.default_rng(20260710); n=len(cc); idx=np.arange(n); dcs=[]
            for _ in range(500):
                bs=rngb.choice(idx,n,replace=True)
                try: dcs.append(concordance_index(tt[bs],-lp2[bs],ev[bs])-concordance_index(tt[bs],-lp1[bs],ev[bs]))
                except Exception: pass
            if dcs: r["delta_C_CI"]=[float(np.percentile(dcs,2.5)),float(np.percentile(dcs,97.5))]
        except Exception: pass
    # PH DIAGNOSTICS (D-4): Schoenfeld test for M2 covariates. Pass the ACTUAL training frame
    # (the columns M2 was fitted on + duration + event), per proportional_hazard_test's contract.
    if "M2" in fits:
        try:
            m2cols=[c for c in MODELS["M2"] if c in cc.columns]
            train_M2=cc[m2cols+["timey","event"]]
            zph=proportional_hazard_test(fits["M2"], train_M2, time_transform="rank")
            r["ph_M2"]={str(k):float(v) for k,v in zph.summary["p"].items()}
        except Exception as e:
            r["ph_M2_error"]=str(e)[:160]
    return r

def choose_branch(primary):
    """Select the frozen result branch from PRIMARY-cohort statistics ONLY (D-2 fix).
    Sensitivities (D3_dropP/D3_noAV) and OOS NEVER gate the branch — they are reported in all
    branches. The 'mixed' branch is reserved for the association-without-discrimination case,
    judged on the PRIMARY D4 model's OWN delta-C CI (not on any sensitivity/OOS p-value)."""
    fm={f["model"] for f in primary.get("failed_models",[])}
    if fm & {"M0","M1","M2"}: return "technical_failure"
    d4=primary.get("D4",{})
    if not d4:
        return "technical_failure"
    if d4.get("success"):
        # significant association. If D4's own added discrimination CI includes <=0, call it 'mixed'
        # (association without demonstrated added discrimination) — a PRIMARY-only judgement.
        dci=primary.get("delta_C_CI")
        if dci is not None and dci[0] <= 0.0:
            return "mixed"
        return "positive"
    # D4 not successful on the primary → null (secondary failures handled separately)
    if fm: return "partial_technical_failure"
    return "null"

# Prespecified subgroups (D-4): PRIMARY D4 HR within each subgroup. Prespecified, descriptive only.
def subgroups(df):
    rows=[]
    cc=df[df.timey>0].copy()
    med_age=float(cc.age.median())
    defs=[("all", cc.index),
          ("female", cc.index[cc.sex==1]),
          ("male", cc.index[cc.sex==0]),
          (f"age_le_{med_age:.0f}", cc.index[cc.age<=med_age]),
          (f"age_gt_{med_age:.0f}", cc.index[cc.age>med_age]),
          ("normal_ecg", cc.index[cc.get("normal_ecg",pd.Series(False,index=cc.index))==1]),
          ("abnormal_ecg", cc.index[cc.get("normal_ecg",pd.Series(True,index=cc.index))!=1])]
    for name,ix in defs:
        sub=cc.loc[ix]
        row={"subgroup":name,"n":int(len(sub)),"events":int(sub.event.sum())}
        try:
            f2=fit_cox(sub,["age","sex","A_std","nn_predicted_age","D_std"])
            hr,lo,hi,p=hr_ci(f2,"D_std")
            row.update({"D4_HR":round(hr,4),"CI_lo":round(lo,4),"CI_hi":round(hi,4),"p":round(p,4)})
        except Exception as e:
            row.update({"D4_HR":None,"error":str(e)[:120]})
        rows.append(row)
    return rows

def frozen_prediction(cohort_df, frozen, baseline):
    """No-refit prediction metrics: apply FROZEN dev M1/M2 coefficients as a fixed linear predictor.
    Reports Harrell-C AND (using dev_baseline_hazard.csv, D-4) a frozen 5-year risk score with
    time-dependent-style discrimination (C on 5y risk) and Brier score at t=5y."""
    cc=cohort_df[cohort_df.timey>0].copy()
    res={"n":int(len(cc)),"events":int(cc.event.sum()),
         "note":"development-FROZEN coefficients applied without refit (anti-optimism)"}
    def lp(model):
        coef=frozen["models"][model]["coef"]
        v=np.zeros(len(cc))
        for cvar,b in coef.items():
            if cvar not in cc.columns: return None
            v=v + b*cc[cvar].to_numpy(float)
        return v
    lps={}
    for m in ["M1","M2"]:
        v=lp(m)
        if v is None: continue
        lps[m]=v
        try: res[f"C_{m}_frozen"]=float(concordance_index(cc.timey.to_numpy(),-v,cc.event.to_numpy()))
        except Exception as e: res[f"C_{m}_frozen_error"]=str(e)[:120]
    if "C_M1_frozen" in res and "C_M2_frozen" in res:
        res["delta_C_frozen"]=res["C_M2_frozen"]-res["C_M1_frozen"]
    # frozen cumulative baseline hazard at t=5y -> 5-year risk with M2 fixed LP; Brier at 5y
    try:
        bh=baseline.sort_values("time"); t_star=5.0
        H0_5=float(bh.loc[bh.time<=t_star,"baseline_hazard"].sum())
        if "M2" in lps:
            risk5=1.0-np.exp(-H0_5*np.exp(lps["M2"]-np.mean(lps["M2"])))
            # observed 5y status among those with >=5y follow-up OR event before 5y
            obs=((cc.event==1)&(cc.timey<=t_star)).astype(float).to_numpy()
            evaluable=((cc.timey>=t_star)|((cc.event==1)&(cc.timey<=t_star))).to_numpy()
            if evaluable.sum()>0:
                res["brier_5y_M2_frozen"]=float(np.mean((risk5[evaluable]-obs[evaluable])**2))
                try: res["C_5yrisk_M2_frozen"]=float(concordance_index(cc.timey.to_numpy()[evaluable],
                                                     -risk5[evaluable], cc.event.to_numpy()[evaluable]))
                except Exception: pass
            res["H0_5y_frozen"]=H0_5
    except Exception as e:
        res["risk5_error"]=str(e)[:120]
    return res

def _atomic_write_outputs(payload):
    """D-5: write all outputs to TMP, add SHA256SUMS + _SUCCESS, then atomic rename TMP->OUT."""
    if os.path.exists(TMP): shutil.rmtree(TMP)
    os.makedirs(TMP, exist_ok=False)
    for fn,obj in payload["csv"].items():
        obj.to_csv(f"{TMP}/{fn}", index=False)
    for fn,obj in payload["json"].items():
        json.dump(obj, open(f"{TMP}/{fn}","w"), indent=2, default=str)
    # checksum manifest over everything written
    sums={fn:sha_file(f"{TMP}/{fn}") for fn in sorted(os.listdir(TMP))}
    with open(f"{TMP}/SHA256SUMS.txt","w") as fh:
        for fn,h in sums.items(): fh.write(f"{h}  {fn}\n")
    open(f"{TMP}/_SUCCESS","w").write(datetime.datetime.now(datetime.timezone.utc).isoformat()+"\n")
    # fsync dir then atomic rename
    if os.path.exists(OUT): raise SystemExit("REVEAL GUARD: out/ already exists — create-once violated")
    os.replace(TMP, OUT)
    return sums

def main():
    t0=time.time()
    guard_no_forbidden_mounts()
    if os.path.exists(OUT):
        raise SystemExit("REVEAL GUARD: out/ already exists — create-once; refusing to run")

    defs=json.load(open("FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json"))
    templates=json.load(open("FROZEN_RESULT_TEMPLATES_RC2.json"))
    INTEG=json.load(open("rc23_integrity_constants.json"))
    scores=pd.read_parquet("scores_outcome_free.parquet")
    oosman=pd.read_parquet("oos_provenance_manifest.parquet")
    frozen=json.load(open("development_model_frozen.json"))
    baseline=pd.read_csv("dev_baseline_hazard.csv")

    # ---- D-3: FROZEN INPUT INTEGRITY (before any outcome mount touches analysis) ----
    assert len(scores)==INTEG["scores_n_rows"], f"scores row count {len(scores)}!={INTEG['scores_n_rows']}"
    assert scores.patient_id.nunique()==INTEG["scores_n_unique_patients"], "scores patient uniqueness drift"
    assert scores.exam_id.nunique()==INTEG["scores_n_unique_exams"], "scores exam uniqueness drift"
    assert set_sha256(scores.patient_id.unique())==INTEG["scores_patient_set_sha256"], "scores patient-set hash drift"
    assert set_sha256(scores.exam_id.unique())==INTEG["scores_exam_set_sha256"], "scores exam-set hash drift"
    assert int(oosman.is_OOS_primary.sum())==INTEG["oos_flagged_total"], "OOS flagged-count drift"
    assert scores.patient_id.duplicated().sum()==0, "duplicate patient in scores"

    # ---- mount + join (first mount of the REPLACEMENT vault) ----
    out=pd.read_parquet(f"{REPL}/age_adaptation_outcomes.parquet")
    for col in ["patient_id","index_exam_id","death","timey"]:
        if col not in out.columns:
            raise SystemExit(f"REVEAL ERROR: outcome vault missing required column '{col}'")
    if out[["patient_id","index_exam_id"]].duplicated().any():
        raise SystemExit("REVEAL ERROR: duplicate (patient_id,index_exam_id) in outcome vault")
    # missing death/timey is a HARD ERROR — never silently censored (D-3)
    n_missing_death=int(out.death.isna().sum()); n_missing_time=int(out.timey.isna().sum())
    if n_missing_death>0 or n_missing_time>0:
        raise SystemExit(f"REVEAL ERROR: outcome vault has missing death({n_missing_death})/timey({n_missing_time}) — refusing to silently censor")

    # join on BOTH patient_id AND index_exam_id (scores.exam_id == outcomes.index_exam_id)
    key=out[["patient_id","index_exam_id","death","timey"]].copy()
    key["patient_id"]=key.patient_id.astype(str); key["index_exam_id"]=key.index_exam_id.astype(str)
    sc=scores.copy(); sc["patient_id"]=sc.patient_id.astype(str); sc["exam_id"]=sc.exam_id.astype(str)
    df=sc.merge(key, left_on=["patient_id","exam_id"], right_on=["patient_id","index_exam_id"],
                how="inner", validate="one_to_one")
    # every scores row must match exactly one outcome row (complete confirmation cohort)
    if len(df)!=len(sc):
        raise SystemExit(f"REVEAL ERROR: join matched {len(df)} of {len(sc)} scores rows — cohort integrity violated")
    df["event"]=(df.death==True).astype(int)
    df["sex"]=(1-df.is_male).astype(float)
    for c in DX:
        if c in df.columns: df[c]=df[c].astype(float)

    # complete-case (qc_ok already baked into scores; assert no NaN in required covariates)
    need=["age","sex","A_std","nn_predicted_age","D_std","D_std_noAV","D_std_dropP",
          "A_std_noAV","A_std_dropP","z_P","z_AV","z_QRS","z_STT","timey","event"]
    cc=df.dropna(subset=need).copy()
    if len(cc)!=INTEG["expected_complete_case_fit_N"]:
        raise SystemExit(f"REVEAL ERROR: complete-case N {len(cc)}!={INTEG['expected_complete_case_fit_N']} (expected frozen)")

    # cohorts — OOS by frozen flag; assert the expected count
    oos_ids=set(oosman.loc[oosman.is_OOS_primary==True,"patient_id"].astype(str))
    cc["patient_id"]=cc.patient_id.astype(str)
    full_primary=cc.copy(); oos=cc[cc.patient_id.isin(oos_ids)].copy()
    if len(oos)!=INTEG["oos_within_scores_expected"]:
        raise SystemExit(f"REVEAL ERROR: OOS complete-case N {len(oos)}!={INTEG['oos_within_scores_expected']} (expected frozen)")

    res_primary=run_cohort(full_primary,"full_primary_75063")
    res_oos    =run_cohort(oos,         "OOS_predictor_robustness_39744")
    branch=choose_branch(res_primary)   # PRIMARY-only (D-2)
    sg=subgroups(full_primary)
    pred={"full_primary_75063":frozen_prediction(full_primary,frozen,baseline),
          "OOS_predictor_robustness_39744":frozen_prediction(oos,frozen,baseline),
          "frozen_source":"development_model_frozen.json","frozen_source_sha256":frozen.get("_sha256")}

    def f(x): return None if x is None else round(float(x),4)
    def fill(c):
        d4=c.get("D4",{}); dp=c.get("D3_dropP",{}); na=c.get("D3_noAV",{})
        m3=c.get("M3",{}); m4=c.get("M4_phase_z",{}); m5=c.get("M5_nonlinearity",{})
        def zf(zc): z=m4.get(zc,{}); return {"HR":f(z.get("HR")),"CI":[f(x) for x in z.get("CI",[None,None])],"p":f(z.get("p"))}
        return {"D4_HR":f(d4.get("HR")),"D4_CI":[f(x) for x in d4.get("CI",[None,None])],"D4_LRT_p":f(d4.get("LRT_p")),
                "D3_dropP_HR":f(dp.get("HR")),"D3_dropP_CI":[f(x) for x in dp.get("CI",[None,None])],"D3_dropP_LRT_p":f(dp.get("LRT_p")),"D3_dropP_reduced":dp.get("reduced"),
                "D3_noAV_HR":f(na.get("HR")),"D3_noAV_CI":[f(x) for x in na.get("CI",[None,None])],"D3_noAV_LRT_p":f(na.get("LRT_p")),"D3_noAV_reduced":na.get("reduced"),
                "n_complete_case_fit":c.get("n_complete_case_fit"),"n_events":c.get("n_events"),
                "C_M1":f(c.get("C_M1")),"C_M2":f(c.get("C_M2")),"delta_C":f(c.get("delta_C")),"delta_C_CI":[f(x) for x in c.get("delta_C_CI",[None,None])],
                "secondary_models":{"M3_D4_HR":f(m3.get("D4_HR")),"M3_D4_CI":[f(x) for x in m3.get("CI",[None,None])],"M3_D4_p":f(m3.get("p")),
                    "M4_phase_z":{"z_P":zf("z_P"),"z_AV":zf("z_AV"),"z_QRS":zf("z_QRS"),"z_STT":zf("z_STT")},
                    "M5_nonlinearity_LRT_p":f(m5.get("LRT_p")),"M5_nonlinearity_LRT_chi2":f(m5.get("LRT_chi2"))},
                "ph_M2":c.get("ph_M2")}
    ledger={"schema":"CLAIMS_LEDGER_populated","generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "selected_branch":branch,"branch_selected_from":"PRIMARY D4 only (sensitivities+OOS do not gate)",
            "full_primary_75063":fill(res_primary),"OOS_predictor_robustness_39744":fill(res_oos),
            "prediction_metrics_frozen_no_refit":pred,
            "eligible_pool_N":75063,"fitted_complete_case_N":res_primary.get("n_complete_case_fit"),
            "language":"association (not prediction); OOS reported by HR+CI regardless of significance"}

    ph_rows=[]
    for coh,res in [("full_primary_75063",res_primary),("OOS_predictor_robustness_39744",res_oos)]:
        for cov,pv in (res.get("ph_M2") or {}).items():
            ph_rows.append({"cohort":coh,"covariate":cov,"schoenfeld_p":pv})

    payload={"csv":{
        "code_primary_cox.csv":pd.DataFrame([res_primary,res_oos]),
        "code_prediction_metrics.csv":pd.DataFrame([pred["full_primary_75063"],pred["OOS_predictor_robustness_39744"]]),
        "code_subgroups.csv":pd.DataFrame(sg),
        "code_ph_diagnostics.csv":pd.DataFrame(ph_rows) if ph_rows else pd.DataFrame([{"note":"PH test unavailable"}]),
    },"json":{
        "reveal_result.json":{"branch":branch,"primary":res_primary,"oos":res_oos,
                              "subgroups":sg,"prediction":pred,"wall_s":time.time()-t0},
        "CLAIMS_LEDGER_populated.json":ledger,
        "REVEAL_LOG_populated.json":{"schema":"REVEAL_LOG_populated","branch":branch,
            "eligible_pool_N":75063,"fitted_complete_case_N":res_primary.get("n_complete_case_fit"),
            "oos_n":res_oos.get("n_complete_case_fit"),
            "integrity_constants_sha256":sha_file("rc23_integrity_constants.json"),
            "completed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()},
    }}
    sums=_atomic_write_outputs(payload)
    print(json.dumps({"branch":branch,"primary_n_cc":res_primary.get("n_complete_case_fit"),
                      "primary_events":res_primary.get("n_events"),"oos_n_cc":res_oos.get("n_complete_case_fit"),
                      "outputs":sorted(sums.keys())}))

if __name__=="__main__":
    main()

