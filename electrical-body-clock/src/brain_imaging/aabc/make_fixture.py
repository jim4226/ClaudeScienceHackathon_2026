"""
Schema-faithful SIMULATED AABC fixture generator.

Produces CSVs with the EXACT Release-2 layout the real pipeline expects:
  - key column 'x___' == id_event == '<pid>_<visit>'
  - 360 HCP-MMP cortical ROIs (R_*_ROI / L_*_ROI) per cortical file
  - FreeSurfer subcortical columns in ASL/fMRI/aseg
  - four channels: structure (thickness/volume/aseg), myelin, ASL (CBF/ATT),
    rfMRI amplitudes; plus a demographics/covariate table and a SEALED outcome table.

NO real participant data is used. Ages, channel signals, and a controllable
D->gait effect are synthesized so the pipeline can be exercised end to end.

Two regimes:
  regime='planted'  -> baseline D_brain genuinely lowers later gait speed
  regime='null'     -> D_brain has zero true effect on gait
"""
import numpy as np, pandas as pd, os, zipfile, json

CORT_ROIS = None  # filled from real header to guarantee identical columns

def _roi_names_from_headers(struct_zip_path):
    """Borrow the real ROI column names (schema only) so fixture columns match exactly."""
    import zipfile as zf
    with zf.ZipFile(struct_zip_path) as z:
        n = [x for x in z.namelist() if x.endswith("Cortical_Areal_Thicknesses.csv") and not x.startswith("__MACOSX")][0]
        with z.open(n) as f:
            hdr = pd.read_csv(f, nrows=0)
    return list(hdr.columns)[1:]   # drop key col

SUBCORT = ["THALAMUS_LEFT","CAUDATE_LEFT","PUTAMEN_LEFT","PALLIDUM_LEFT","HIPPOCAMPUS_LEFT",
           "AMYGDALA_LEFT","ACCUMBENS_LEFT","DIENCEPHALON_VENTRAL_LEFT","THALAMUS_RIGHT",
           "CAUDATE_RIGHT","PUTAMEN_RIGHT","PALLIDUM_RIGHT","HIPPOCAMPUS_RIGHT",
           "AMYGDALA_RIGHT","ACCUMBENS_RIGHT","DIENCEPHALON_VENTRAL_RIGHT"]
ASEG_COLS = ["FS_L_Lateral-Ventricle","FS_L_Hippocampus","FS_L_Amygdala","FS_L_Thalamus",
             "FS_L_Caudate","FS_L_Putamen","FS_R_Hippocampus","FS_R_Amygdala","FS_R_Thalamus",
             "FS_R_Caudate","FS_R_Putamen","BrainSegVol","EstimatedTotalIntraCranialVol"]
SITES = ["MGH","UCLA","Uminn","WashU"]

def make_fixture(outdir, roi_names, n_participants=900, regime="planted", seed=7):
    rng = np.random.default_rng(seed)
    os.makedirs(outdir, exist_ok=True)
    P = n_participants
    pid = np.array([f"HCA{100000+i}" for i in range(P)])
    true_age = rng.uniform(36, 90, P)
    sex = rng.choice(["M","F"], P)
    site = rng.choice(SITES, P)
    educ = np.clip(rng.normal(16, 3, P), 6, 22).round()
    height = rng.normal(67, 4, P); bmi = np.clip(rng.normal(27,4,P),16,45)

    # visit structure mimicking AABC (V1 all; V2 ~65%; V3 ~34%; V4 ~7%)
    nvis = rng.choice([1,2,3,4], P, p=[0.30,0.33,0.30,0.07])
    # per-participant latent aging rates + a latent "disagreement" propensity
    disagree_prop = rng.normal(0,1,P)                # latent, per participant
    # channel-specific latent aging (correlated + channel drift)
    shared = rng.normal(0,1,P)

    rows_demo, rows_out = [], []
    ch_rows = {c: [] for c in ["thick","vol","myelin","cbf","att","rfmri","aseg"]}
    # ---- FIXED per-channel spatial loadings (generated ONCE, shared across all
    #      participants/visits). This is the key generative-model correctness point:
    #      which ROIs carry age must be constant across samples or no clock can learn it.
    nR = len(roi_names); nA = nR + len(SUBCORT)
    def fixed_loadings(n, k=40, diffuse=0.15):
        w = np.zeros(n)
        strong = rng.choice(n, min(k,n), replace=False)
        w[strong] = rng.normal(0, 1.0, min(k,n))          # strong concentrated loadings
        w += diffuse*rng.normal(0,1,n)*(rng.random(n)<0.5)  # weak diffuse loadings
        return w
    W = {"thick": fixed_loadings(nR), "vol": fixed_loadings(nR), "myelin": fixed_loadings(nR),
         "cbf": fixed_loadings(nA), "att": fixed_loadings(nA), "rfmri": fixed_loadings(nA)}
    # fixed disagreement DIRECTION per channel (unit-ish vector)
    Wd = {k: rng.normal(0,1,len(W[k])) for k in W}

    def roi_block(key, base, gap, scale, sign, r_target, zage):
        """base intensity + concentrated age signal (fixed loadings) + disagreement + noise.
        latent = observed-brain-age tracking true age at ~r_target (per-visit scalar)."""
        n = len(W[key])
        latent = r_target*zage + np.sqrt(max(1e-6,1-r_target**2))*rng.normal()
        return (base
                + sign*scale*2.0*latent*W[key]                     # concentrated age signal
                + gap*scale*0.4*Wd[key]/np.sqrt(n)                 # disagreement direction
                + rng.normal(0, scale*0.8, n))                    # per-ROI noise

    for i in range(P):
        for v in range(nvis[i]):
            visit = f"V{v+1}"
            ide = f"{pid[i]}_{visit}"
            age_v = min(true_age[i] + v*rng.uniform(1.0,2.5), 90)
            days = 0 if v==0 else int(v*rng.uniform(300,800))
            # channel "brain age gap" signals: shared drift (-> A) + channel-specific
            # DIVERGENT disagreement (-> D). disagree_prop pushes the 4 channels along a
            # FIXED divergent pattern (+,-,+,-) so a high-propensity participant has large
            # realized z-spread == large D_brain (the quantity the pipeline measures).
            dp = disagree_prop[i]
            gS = 0.9*shared[i] + 1.3*dp + rng.normal(0,0.35)
            gM = 0.9*shared[i] - 1.3*dp + rng.normal(0,0.35)
            gP = 0.8*shared[i] + 1.3*dp + rng.normal(0,0.40)
            gF = 0.7*shared[i] - 1.3*dp + rng.normal(0,0.45)
            zage = (age_v - 63)/15.0   # standardized age
            ch_rows["thick"].append([ide]+list(roi_block("thick", 2.5, gS, 0.25, -1, 0.72, zage)))
            ch_rows["vol"].append([ide]+list(roi_block("vol", 3000, gS, 200, -1, 0.72, zage)))
            ch_rows["myelin"].append([ide]+list(roi_block("myelin", 1.4, gM, 0.12, -1, 0.60, zage)))
            ch_rows["cbf"].append([ide]+list(roi_block("cbf", 50, gP, 8, -1, 0.55, zage)))
            ch_rows["att"].append([ide]+list(roi_block("att", 1.5, gP, 0.2, 1, 0.55, zage)))
            ch_rows["rfmri"].append([ide]+list(roi_block("rfmri", 1.0, gF, 0.15, -1, 0.50, zage)))
            ch_rows["aseg"].append([ide]+list(2500 - 1.5*(age_v-63) + gS*10 + rng.normal(0,40,len(ASEG_COLS))))
            rows_demo.append(dict(id_event=ide, id=pid[i], event=visit, age_open=round(age_v,1),
                                  sex=sex[i], site=site[i], scanner=f"{site[i]}_3T",
                                  education=educ[i], height_inches=round(height[i],1),
                                  bmi=round(bmi[i],1), days_from_V1=days))
            # SEALED OUTCOME: gait speed declines w/ age + (regime) disagreement.
            # Planted effect acts on the DECLINE RATE (a slope, not a level): higher baseline
            # |disagreement| -> faster gait-speed decline per year since V1. A level effect
            # would cancel in the annualized-change primary, so it must be time-scaled.
            yrs = days/365.25
            base_speed = 1.2 - 0.006*(age_v-63)
            d_effect = (-0.06*abs(disagree_prop[i])*yrs) if regime=="planted" else 0.0
            speed = base_speed + d_effect + rng.normal(0,0.06)
            secs = 4.0/max(speed,0.2)
            rows_out.append(dict(id_event=ide,
                                 tlbx_walk_4_rawscore=round(secs,3),
                                 tlbx_walk_2_rawscore=round(120*speed+rng.normal(0,8),1),
                                 tlbx_grip_dominant_score=round(rng.normal(70-0.3*(age_v-63),12),1),
                                 moca_sum=int(np.clip(rng.normal(27-0.05*(age_v-63),2),10,30))))

    cort_cols = roi_names
    asl_cols = roi_names + SUBCORT
    def W(name, rows, cols):
        df = pd.DataFrame(rows, columns=["x___"]+cols); df.to_csv(os.path.join(outdir,name), index=False); return df
    W("Cortical_Areal_Thicknesses.csv", ch_rows["thick"], cort_cols)
    W("Cortical_Areal_Volumes.csv", ch_rows["vol"], cort_cols)
    W("Cortical_Areal_Myelin.csv", ch_rows["myelin"], cort_cols)
    W("PVEc_ASL_CBF.csv", ch_rows["cbf"], asl_cols)
    W("PVEc_ASL_ATT.csv", ch_rows["att"], asl_cols)
    W("rfMRI_REST_FullAmplitudes.csv", ch_rows["rfmri"], asl_cols)
    W("asegstats.csv", ch_rows["aseg"], ASEG_COLS)
    demo = pd.DataFrame(rows_demo); demo.to_csv(os.path.join(outdir,"demographics.csv"), index=False)
    out = pd.DataFrame(rows_out); out.to_csv(os.path.join(outdir,"SEALED_NIH-Toolbox-Scores.csv"), index=False)
    meta = dict(regime=regime, n_participants=P, n_visits=len(demo), seed=seed,
                n_cort_roi=len(cort_cols), n_asl_cols=len(asl_cols))
    json.dump(meta, open(os.path.join(outdir,"_fixture_meta.json"),"w"), indent=2)
    return meta
