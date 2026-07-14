"""
NeuroMotionVector driver: wires the frozen pipeline to a data folder.

Usage (real or fixture):
    python run_pipeline.py --data <folder> --out <folder> [--sealed-outcome <csv>]

The --data folder must contain the channel CSVs (real Release-2 names or the
fixture's). The outcome CSV is passed SEPARATELY and is only opened after the
geometry is frozen+hashed. Phase B refuses to run otherwise.
"""
import argparse, json, os, sys
import numpy as np, pandas as pd

def _load_module(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m)
    return m

def channel_files(data):
    j = lambda f: os.path.join(data, f)
    return {
        "S_structure": [j("Cortical_Areal_Thicknesses.csv"), j("Cortical_Areal_Volumes.csv"), j("asegstats.csv")],
        "M_myelin":    [j("Cortical_Areal_Myelin.csv")],
        "P_perfusion": [j("PVEc_ASL_CBF.csv"), j("PVEc_ASL_ATT.csv")],
        "F_function":  [j("rfMRI_REST_FullAmplitudes.csv")],
    }

def run(data, out, sealed_outcome, pipe_path, fast=False):
    P = _load_module(pipe_path, "nmv_pipe")
    os.makedirs(out, exist_ok=True)
    log = {}

    # ---------- PHASE A (OUTCOME-BLIND) ----------
    cf = channel_files(data)
    mats = P.load_channel_matrix(cf)
    demo = pd.read_csv(os.path.join(data, "demographics.csv"))
    ages = dict(zip(demo["id_event"], demo["age_open"]))
    manifest = P.build_manifest(mats, demo)
    manifest.to_parquet(os.path.join(out, "aabc_participant_visit_manifest.parquet"))

    split = P.hash_split(sorted(manifest["id"].unique()))
    gate = P.availability_gate(manifest, split)
    log["availability_gate"] = gate

    geom, scored = P.build_geometry(mats, manifest, split, ages, fast=fast)
    log["clock_metrics"] = geom.clock_metrics
    log["n_clocks_passed"] = geom.n_clocks_passed
    log["frozen_hash"] = geom.frozen_hash

    # clock metrics table
    cm = pd.DataFrame(geom.clock_metrics).T.reset_index().rename(columns={"index":"channel"})
    cm.to_csv(os.path.join(out, "brain_channel_clock_metrics.csv"), index=False)
    # scores (A/D/z) — aggregate, no outcome
    scored.to_parquet(os.path.join(out, "neuromotionvector_scores.parquet"))

    # inventory (aggregate counts only)
    inv = manifest.groupby("event")[[f"has_{c}" for c in P.CHANNELS]+["has_all4"]].sum()
    inv["n_visits"] = manifest.groupby("event").size()
    inv.reset_index().to_csv(os.path.join(out, "aabc_data_inventory.csv"), index=False)

    # ---------- FREEZE WALL ----------
    frozen_marker = os.path.join(out, "GEOMETRY_FROZEN.json")
    json.dump({"frozen_hash": geom.frozen_hash, "n_clocks_passed": geom.n_clocks_passed,
               "clock_metrics": geom.clock_metrics}, open(frozen_marker,"w"), indent=2)

    # ---------- PHASE B (SEALED) ----------
    if sealed_outcome and geom.n_clocks_passed >= P.MIN_CLOCKS_PASS:
        outcomes = pd.read_csv(sealed_outcome).set_index("id_event")
        covariates = demo.set_index("id_event")[["sex","site","education","height_inches","bmi","days_from_V1"]]
        cov = covariates.copy()
        # --- sex -> 0/1 (accept 'M'/'F', 'Male'/'Female', or 1/2 numeric codes) ---
        sx = cov["sex"].astype(str).str.upper().str.strip()
        cov["sex"] = sx.isin(["M","MALE","1"]).astype(float)
        # --- education -> ordinal rank (natural order; unknown -> NaN, dropped by regressions) ---
        EDU_ORDER = ["no formal","primary","some secondary","secondary","beyond secondary"]
        def edu_rank(v):
            s=str(v).lower()
            for i,k in enumerate(EDU_ORDER):
                if k in s: return float(i)
            try: return float(v)          # already-numeric education
            except (ValueError, TypeError): return np.nan
        cov["education"] = cov["education"].map(edu_rank)
        # --- numeric coercion for continuous covariates ---
        for c in ["height_inches","bmi","days_from_V1"]:
            cov[c] = pd.to_numeric(cov[c], errors="coerce")
        # --- site -> dummies (drop_first); coerce all to float ---
        cov = pd.get_dummies(cov, columns=["site"], drop_first=True)
        for c in cov.columns:
            cov[c] = pd.to_numeric(cov[c], errors="coerce")
        cov = cov.astype(float)
        # attach days_from_V1 into scored for longitudinal Δt
        scored2 = scored.copy()
        scored2["days_from_V1"] = demo.set_index("id_event")["days_from_V1"].reindex(scored2.index).values
        for c in ["sex","education","height_inches","bmi"]:
            scored2[c] = cov[c].reindex(scored2.index).values if c in cov else np.nan
        for sc in [c for c in cov.columns if c.startswith("site_")]:
            scored2[sc] = cov[sc].reindex(scored2.index).values

        prim_long = P.run_primary_longitudinal(geom, scored2, outcomes, cov)
        prim_xsec = P.run_primary_crosssectional(geom, scored2, outcomes, cov)
        secs = P.run_secondaries(geom, scored2, outcomes, cov)
        sens = P.run_sensitivities(geom, scored2, outcomes, cov)

        primary = prim_long if prim_long.get("status")=="RUN" else prim_xsec
        pd.DataFrame([{**primary, "role":"PRIMARY"},
                      {**prim_xsec, "role":"cross_sectional"}]).to_csv(
            os.path.join(out,"neuromotionvector_primary_result.csv"), index=False)
        pd.DataFrame(secs).to_csv(os.path.join(out,"neuromotionvector_secondaries.csv"), index=False)
        pd.DataFrame(sens).to_csv(os.path.join(out,"neuromotionvector_sensitivities.csv"), index=False)
        log["primary"] = primary; log["secondaries"]=secs; log["sensitivities"]=sens
    else:
        log["phase_b"] = "SKIPPED — no sealed outcome provided or <3 clocks passed"

    json.dump(log, open(os.path.join(out,"run_log.json"),"w"), indent=2, default=float)
    return log

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sealed-outcome", default=None)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--pipe", default=os.path.join(os.path.dirname(__file__),"neuromotionvector_pipeline.py"))
    a = ap.parse_args()
    L = run(a.data, a.out, a.sealed_outcome, a.pipe, fast=a.fast)
    print(json.dumps(L, indent=2, default=float)[:2000])
