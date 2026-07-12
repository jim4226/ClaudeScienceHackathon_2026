"""
Analysis for The Electrical Body Clock (Act I) — consumes models/test_predictions.csv
(per-ECG chronological age + predicted age & age-gap for whole/p/pr/qrs/stt) joined to
cohort_manifest.csv (six disease-group labels).

Produces the paper's core results:
  1. clock_performance.csv        — MAE / R / R^2 per subsystem clock vs whole-beat baseline
  2. gap_correlation matrix       — are the four subsystem age-gaps independent?
  3. DISEASE-SUBSTRATE MATRIX     — mean age-gap (z) per (disease group x subsystem clock),
                                    tests the specificity hypothesis: does atrial disease
                                    selectively age the P clock, AV block the PR clock, etc.
  4. figures                      — performance bars, gap-correlation heatmap, substrate matrix
"""
import numpy as np, pandas as pd
from scipy import stats

MODELS="drive_staging/ptbxl/models"
MANIFEST="drive_staging/ptbxl/cohort_manifest.csv"
SUB=["whole","p","pr","qrs","stt"]
SUBSYS_CLOCKS=["p","pr","qrs","stt"]
GROUPS=["atrial_disease","av_conduction_disease","ventricular_conduction_disease",
        "hypertrophy","ischemia_or_stt_abnormality","myocardial_infarction"]
# hypothesised primary substrate for each disease group (for the diagonal test)
PRIMARY={"atrial_disease":"p","av_conduction_disease":"pr",
         "ventricular_conduction_disease":"qrs","hypertrophy":"qrs",
         "ischemia_or_stt_abnormality":"stt","myocardial_infarction":"stt"}

def load():
    pred=pd.read_csv(f"{MODELS}/test_predictions.csv")
    man=pd.read_csv(MANIFEST)
    df=pred.merge(man[["ecg_id","sex","strat_fold"]+GROUPS], on="ecg_id", how="left")
    df["any_disease"]=df[GROUPS].max(axis=1)
    df=bias_correct(df)
    return df

def bias_correct(df):
    """
    Cole/de Lange age-bias correction. The age-prediction bias (regression to the mean:
    under-predict old, over-predict young) is a property of the MODEL, present in everyone.
    Fit gap = a*age + b on DISEASE-FREE CONTROLS (the healthy aging reference), then
    subtract that expected bias from EVERYONE's gap. The corrected gap 'cgap_X' is then
    'how much older/younger this subsystem looks than a healthy person of the same age'.
    Positive = accelerated electrical aging.
    """
    ctrl=df[df["any_disease"]==0]
    for s in SUBSYS_CLOCKS+["whole"]:
        g=f"gap_{s}"
        if g not in df: continue
        a,b=np.polyfit(ctrl["age"], ctrl[g], 1)          # bias line from controls
        df[f"cgap_{s}"]=df[g]-(a*df["age"]+b)            # residual vs healthy trajectory
    return df

def performance(df):
    rows=[]
    for s in SUB:
        pc=f"pred_{s}"
        if pc not in df: continue
        mae=(df[pc]-df["age"]).abs().mean()
        r=stats.pearsonr(df[pc],df["age"])[0]
        rows.append(dict(clock=s, MAE=round(mae,3), R=round(r,3), R2=round(r*r,3), n=len(df)))
    return pd.DataFrame(rows)

def gap_corr(df, corrected=True):
    pre="cgap_" if corrected else "gap_"
    G=[f"{pre}{s}" for s in SUBSYS_CLOCKS if f"{pre}{s}" in df]
    C=df[G].corr()
    C.index=[c.replace(pre,"") for c in C.index]; C.columns=C.index
    return C

def substrate_matrix(df):
    """
    For each disease group (rows) x subsystem clock (cols): standardized mean age-gap
    among cases, i.e. does having disease X inflate the age-gap of clock Y beyond controls?
    Reported as Cohen's d (cases vs controls) so cells are comparable.
    """
    d=np.zeros((len(GROUPS),len(SUBSYS_CLOCKS)))
    p=np.zeros_like(d)
    for i,g in enumerate(GROUPS):
        cases=df[df[g]==1]; ctrl=df[df["any_disease"]==0]   # vs DISEASE-FREE controls
        for j,s in enumerate(SUBSYS_CLOCKS):
            gap=f"cgap_{s}"                                   # bias-corrected age-gap
            a=cases[gap].dropna(); b=ctrl[gap].dropna()
            # Cohen's d
            n1,n2=len(a),len(b); s1,s2=a.std(),b.std()
            sp=np.sqrt(((n1-1)*s1**2+(n2-1)*s2**2)/(n1+n2-2)) if n1+n2>2 else np.nan
            d[i,j]=(a.mean()-b.mean())/sp if sp and sp>0 else np.nan
            p[i,j]=stats.mannwhitneyu(a,b,alternative="two-sided")[1] if n1>5 and n2>5 else np.nan
    D=pd.DataFrame(d, index=GROUPS, columns=SUBSYS_CLOCKS)
    P=pd.DataFrame(p, index=GROUPS, columns=SUBSYS_CLOCKS)
    return D,P

def specificity_test(D):
    """Is the hypothesised primary substrate the LARGEST age-gap in its row? (diagonal wins)"""
    hits=[]
    for g in GROUPS:
        row=D.loc[g]
        winner=row.idxmax()
        hits.append(dict(disease=g, hypothesised=PRIMARY[g], observed_max=winner,
                         match=winner==PRIMARY[g], d_hyp=round(row[PRIMARY[g]],3),
                         d_max=round(row[winner],3)))
    return pd.DataFrame(hits)

if __name__=="__main__":
    df=load()
    perf=performance(df); perf.to_csv(f"{MODELS}/clock_performance.csv",index=False)
    print("=== PERFORMANCE ==="); print(perf.to_string(index=False))
    C=gap_corr(df); C.to_csv(f"{MODELS}/gap_correlation.csv")
    print("\n=== GAP CORRELATION ==="); print(C.round(2).to_string())
    D,P=substrate_matrix(df)
    D.to_csv(f"{MODELS}/substrate_matrix_d.csv"); P.to_csv(f"{MODELS}/substrate_matrix_p.csv")
    print("\n=== DISEASE-SUBSTRATE MATRIX (Cohen's d, cases vs controls) ===")
    print(D.round(2).to_string())
    spec=specificity_test(D); spec.to_csv(f"{MODELS}/specificity_test.csv",index=False)
    print("\n=== SPECIFICITY TEST (does disease age its hypothesised substrate most?) ===")
    print(spec.to_string(index=False))
    print(f"\nspecificity hits: {spec.match.sum()}/{len(spec)}")
