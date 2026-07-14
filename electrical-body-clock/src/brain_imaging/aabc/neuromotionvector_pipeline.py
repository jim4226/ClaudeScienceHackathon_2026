"""
NeuroMotionVector — frozen, outcome-blind analysis pipeline.

Governed by NEUROMOTIONVECTOR_PROTOCOL_LOCK.json (self_sha256 c5d2b30f...).

DESIGN PRINCIPLE — auditable outcome-blinding
---------------------------------------------
The code is split into two phases with a hard wall between them:

  Phase A  (geometry, OUTCOME-BLIND)
     load_channels -> build_manifest -> availability_gate -> hash_split
     -> train_channel_clocks -> freeze_bias_correction -> compute_A_D
     -> FrozenGeometry (hashed)
     NONE of these functions accept, import, or read any outcome
     (gait/grip/endurance/cognition) variable.

  Phase B  (outcome, SEALED)
     run_primary / run_secondaries / run_sensitivities
     Every Phase-B function REQUIRES a FrozenGeometry whose hash is
     verified before it will touch the outcome file. If the geometry
     is not frozen, Phase B refuses to run.

This means the outcome file is provably unopened until the geometry
(clocks + bias + covariance + standardization) is frozen and hashed.
"""
from __future__ import annotations
import hashlib, json, warnings
from dataclasses import dataclass, field, asdict
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.covariance import LedoitWolf
from scipy import stats

# ----------------------------------------------------------------------
# Frozen constants from the protocol lock
# ----------------------------------------------------------------------
CHANNELS = ["S_structure", "M_myelin", "P_perfusion", "F_function"]

# Helmert contrast matrix C: C·1 = 0, C·C^T = I_3 (rows orthonormal to all-ones)
HELMERT_C = np.array([
    [ 1/np.sqrt(2), -1/np.sqrt(2),        0.0,         0.0],
    [ 1/np.sqrt(6),  1/np.sqrt(6), -2/np.sqrt(6),      0.0],
    [ 1/np.sqrt(12), 1/np.sqrt(12), 1/np.sqrt(12), -3/np.sqrt(12)],
])
SPLIT_SALT = "neuromotionvector-aabc-r2-v1"
SPLIT_FRACS = {"development": 0.60, "calibration": 0.20, "final_test": 0.20}
CLOCK_R_GATE = 0.20          # stop-rule #3
MIN_CLOCKS_PASS = 3          # stop-rule #3 / #10
MIN_BASELINE_COMPLETE = 500  # stop-rule #2
MIN_LONGITUDINAL_HOLDOUT = 150  # revised stop-rule #5

# ----------------------------------------------------------------------
# Phase A — participant split (outcome-blind)
# ----------------------------------------------------------------------
def hash_split(participant_ids, salt=SPLIT_SALT, fracs=SPLIT_FRACS) -> dict:
    """Deterministic participant-grouped split. ALL visits of a participant
    land in the same partition. Uses sha256(salt+id) -> uniform(0,1)."""
    out = {}
    c_dev = fracs["development"]
    c_cal = c_dev + fracs["calibration"]
    for pid in participant_ids:
        h = hashlib.sha256(f"{salt}:{pid}".encode()).hexdigest()
        u = int(h[:16], 16) / 16**16
        out[pid] = ("development" if u < c_dev
                    else "calibration" if u < c_cal
                    else "final_test")
    return out


# ----------------------------------------------------------------------
# Phase A — channel loading (OUTCOME-BLIND: only predictor IDPs)
# ----------------------------------------------------------------------
def _parse_id_event(s: pd.Series):
    """id_event like 'HCA1234_V1' -> (participant_id, event)."""
    id_ = s.astype(str).str.replace(r"_(V\d+|AF\d+|F\d+|CR)$", "", regex=True)
    ev = s.astype(str).str.extract(r"_((?:V|AF|F)\d+|CR)$")[0].fillna("V1")
    return id_, ev

def load_channel_matrix(channel_files: dict, key_aliases=("x___", "Session", "id_event", "id_visit")):
    """Load per-channel predictor matrices, return {channel: DataFrame indexed by id_event}.
    channel_files: {channel_name: [list of csv paths]}. Horizontally concatenates the
    feature CSVs belonging to one channel. Reads ONLY predictor IDPs — never outcomes."""
    mats = {}
    for ch, paths in channel_files.items():
        parts = []
        for p in paths:
            df = pd.read_csv(p)
            keycol = next((k for k in key_aliases if k in df.columns), df.columns[0])
            df = df.rename(columns={keycol: "id_event"})
            # Normalize the join key to the canonical '<participant>_<event>'. Some
            # FreeSurfer/aseg exports suffix the Session id with a scanner tag
            # (e.g. 'HCA6000030_V1_MR'); strip it so all channel parts align on concat.
            df["id_event"] = (df["id_event"].astype(str)
                              .str.replace(r"_(MR|3T|7T)$", "", regex=True))
            df = df.set_index("id_event")
            df = df.select_dtypes(include=[np.number])   # numeric IDPs only
            df = df[~df.index.duplicated(keep="first")]   # guard dup keys before concat
            df.columns = [f"{ch}__{c}" for c in df.columns]
            parts.append(df)
        mats[ch] = pd.concat(parts, axis=1) if parts else pd.DataFrame()
    return mats


def build_manifest(mats: dict, demo: pd.DataFrame):
    """One row per participant-visit. demo carries id_event, id, event, age_open,
    sex, site, scanner, education, height_inches, bmi, days_from_V1.
    Availability flags per channel = row has >=80% non-missing features."""
    demo = demo.copy()
    demo = demo.set_index("id_event")
    # A visit with no chronological age cannot train/score an age clock — it is
    # outside the analysis by definition. Require a valid numeric age_open. (Real
    # AABC exports carry survey-only events and occasional missing ages; the fixture
    # was complete so this only bites on real data.)
    demo["age_open"] = pd.to_numeric(demo["age_open"], errors="coerce")
    n_before = len(demo)
    demo = demo[demo["age_open"].notna()]
    man = demo.copy()
    man.attrs["n_dropped_no_age"] = int(n_before - len(demo))
    for ch, M in mats.items():
        if len(M):
            frac_present = M.reindex(man.index).notna().mean(axis=1)
            man[f"has_{ch}"] = (frac_present >= 0.80).fillna(False)
        else:
            man[f"has_{ch}"] = False
    man["has_all4"] = man[[f"has_{c}" for c in CHANNELS]].all(axis=1)
    man = man.reset_index()
    return man


def availability_gate(manifest: pd.DataFrame, split: dict):
    """Outcome-blind primary selection. Uses availability COUNTS only.
    Longitudinal holdout = participants (in calibration+final) whose baseline
    visit has all-4 channels and who have a later visit."""
    man = manifest.copy()
    man["partition"] = man["id"].map(split)
    # baseline = earliest event per participant
    order = {"V1": 0, "V2": 1, "V3": 2, "V4": 3}
    man["evord"] = man["event"].map(order).fillna(9)
    base = man.sort_values("evord").groupby("id").first()
    n_baseline_all4 = int(base["has_all4"].sum())
    # longitudinal-complete: baseline all4 AND >=2 visits present
    nvis = man.groupby("id")["event"].nunique()
    base_all4_ids = set(base.index[base["has_all4"]])
    long_ids = [i for i in base_all4_ids if nvis.get(i, 0) >= 2]
    holdout_long = [i for i in long_ids if split.get(i) in ("calibration", "final_test")]
    finaltest_all4 = [i for i in base_all4_ids if split.get(i) == "final_test"]

    primary = "longitudinal" if len(holdout_long) >= MIN_LONGITUDINAL_HOLDOUT else "cross_sectional"
    return {
        "n_baseline_all4": n_baseline_all4,
        "n_longitudinal_complete_total": len(long_ids),
        "n_longitudinal_holdout": len(holdout_long),
        "n_finaltest_all4": len(finaltest_all4),
        "baseline_gate_pass": n_baseline_all4 >= MIN_BASELINE_COMPLETE,
        "primary_selected": primary,
        "longitudinal_gate_threshold": MIN_LONGITUDINAL_HOLDOUT,
    }


# ----------------------------------------------------------------------
# Phase A — channel age clocks (OUTCOME-BLIND: target is chronological age)
# ----------------------------------------------------------------------
@dataclass
class ChannelClock:
    channel: str
    feature_names: list
    imputer_median: np.ndarray
    scaler_mean: np.ndarray
    scaler_scale: np.ndarray
    coef: np.ndarray
    intercept: float
    alpha: float
    l1_ratio: float
    heldout_r: float            # r on calibration (truly held out from clock fit)
    cv_r_dev: float             # grouped-CV r within development
    passed: bool

def _prep(X, imp=None, scaler=None, fit=False):
    if fit:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")          # all-NaN column -> NaN median
            imp = np.nanmedian(X, axis=0)
        imp = np.where(np.isnan(imp), 0.0, imp)      # dev-fit fallback for all-NaN features
    Xi = np.where(np.isnan(X), imp, X)
    Xi = np.where(np.isnan(Xi), 0.0, Xi)             # belt-and-suspenders: no NaN reaches the model
    if fit:
        scaler = StandardScaler().fit(Xi)
    Xs = scaler.transform(Xi)
    return Xs, imp, scaler

def train_channel_clock(channel, X_dev, age_dev, groups_dev, X_cal, age_cal, seed=0, fast=False):
    """Fit ElasticNet age clock on DEVELOPMENT only, with participant-grouped
    nested CV for hyperparameters. Held-out performance measured on CALIBRATION.

    fast=False (DEFAULT, for the real run): full 50-alpha x 3-l1_ratio x 5-fold grid.
    fast=True  (fixture/code-validation only): coarse 15-alpha x 2-l1_ratio grid,
               3 folds. Same code path, ~5x faster; NOT for the frozen real analysis."""
    feat = list(X_dev.columns)
    Xd = X_dev.to_numpy(float)
    Xd_s, imp, scaler = _prep(Xd, fit=True)
    n_folds = 3 if fast else 5
    l1_grid = [0.1, 0.9] if fast else [0.1, 0.5, 0.9]
    n_alpha = 15 if fast else 50
    # sklearn 1.9: pass GROUP-AWARE split iterators to cv= (materialized as a list),
    # which avoids the metadata-routing requirement for a `groups` fit kwarg.
    cv_splits = list(GroupKFold(n_splits=n_folds).split(Xd_s, age_dev, groups_dev))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ElasticNetCV(l1_ratio=l1_grid, alphas=n_alpha, cv=cv_splits,
                             random_state=seed, max_iter=5000, n_jobs=-1)
        model.fit(Xd_s, age_dev)
        # honest internal grouped-CV r: one pass with a PLAIN ElasticNet fixed at the
        # tuned hyperparameters (avoids re-tuning the full alpha grid inside every fold —
        # ~10x faster and the number we report is the CV of the selected model).
        from sklearn.linear_model import ElasticNet
        cvpred = cross_val_predict(
            ElasticNet(alpha=model.alpha_, l1_ratio=model.l1_ratio_,
                       random_state=seed, max_iter=5000),
            Xd_s, age_dev, cv=cv_splits)
    cv_r = float(np.corrcoef(cvpred, age_dev)[0, 1])
    # held-out on calibration
    Xc_s, _, _ = _prep(X_cal.to_numpy(float), imp=imp, scaler=scaler)
    pred_cal = model.predict(Xc_s)
    heldout_r = float(np.corrcoef(pred_cal, age_cal)[0, 1])
    return ChannelClock(
        channel=channel, feature_names=feat, imputer_median=imp,
        scaler_mean=scaler.mean_, scaler_scale=scaler.scale_,
        coef=model.coef_, intercept=float(model.intercept_),
        alpha=float(model.alpha_), l1_ratio=float(model.l1_ratio_),
        heldout_r=heldout_r, cv_r_dev=cv_r, passed=(heldout_r >= CLOCK_R_GATE),
    )

def clock_predict(clock: ChannelClock, X: pd.DataFrame):
    X = X.reindex(columns=clock.feature_names)
    Xi = np.where(np.isnan(X.to_numpy(float)), clock.imputer_median, X.to_numpy(float))
    Xs = (Xi - clock.scaler_mean) / clock.scaler_scale
    return Xs @ clock.coef + clock.intercept


# ----------------------------------------------------------------------
# Phase A — bias correction + A/D geometry (OUTCOME-BLIND)
# ----------------------------------------------------------------------
@dataclass
class BiasCorrection:
    channel: str
    alpha: float   # intercept of gap~age on calibration
    beta: float    # slope
    s: float       # residual scale

def fit_bias_correction(channel, gap_cal, age_cal) -> BiasCorrection:
    """z = (gap - alpha - beta*age)/s, all fit on CALIBRATION only.
    Guard s against ~0 (a near-perfect clock leaves ~zero residual scale, which
    would produce inf/NaN z). Floor at a small fraction of the gap SD so the
    channel stays finite; a clock this good simply contributes ~0 disagreement."""
    b, a, *_ = stats.linregress(age_cal, gap_cal)
    resid = gap_cal - (a + b * age_cal)
    s = float(np.std(resid, ddof=1))
    gap_sd = float(np.std(gap_cal, ddof=1))
    s_floor = max(1e-6, 1e-3 * (gap_sd if np.isfinite(gap_sd) and gap_sd > 0 else 1.0))
    if not np.isfinite(s) or s < s_floor:
        s = s_floor
    return BiasCorrection(channel, float(a), float(b), s)

def apply_bias(bc: BiasCorrection, gap, age):
    return (gap - bc.alpha - bc.beta * age) / bc.s

def compute_q_A_D(Z: np.ndarray, sigma_inv: np.ndarray):
    """Z: (n,4) standardized gaps in CHANNELS order. Returns A, D, q."""
    A = Z.mean(axis=1)                       # equal-weight shared axis
    q = Z @ HELMERT_C.T                       # (n,3) contrast coords
    D = np.sqrt(np.einsum("ij,jk,ik->i", q, sigma_inv, q))
    return A, D, q


@dataclass
class FrozenGeometry:
    """Everything needed to score any new participant-visit, plus the audit hash.
    Contains NO outcome information."""
    channels: list
    clocks: dict
    bias: dict
    sigma_q: np.ndarray            # Ledoit-Wolf covariance of calibration q
    sigma_q_inv: np.ndarray
    D_mean_cal: float              # standardization constants (calibration)
    D_std_cal: float
    A_mean_cal: float
    A_std_cal: float
    split_salt: str
    clock_metrics: dict
    n_clocks_passed: int
    frozen_hash: str = ""

    def compute_hash(self):
        h = hashlib.sha256()
        for ch in self.channels:
            c = self.clocks[ch]
            h.update(np.asarray(c.coef).tobytes())
            h.update(np.array([c.intercept, c.alpha, c.l1_ratio]).tobytes())
            b = self.bias[ch]
            h.update(np.array([b.alpha, b.beta, b.s]).tobytes())
        h.update(np.asarray(self.sigma_q).tobytes())
        h.update(np.array([self.D_mean_cal, self.D_std_cal,
                           self.A_mean_cal, self.A_std_cal]).tobytes())
        h.update(self.split_salt.encode())
        return h.hexdigest()

    def freeze(self):
        self.frozen_hash = self.compute_hash()
        return self

    def score(self, Z: np.ndarray):
        """Score standardized-gap matrix Z (n,4) -> DataFrame with A_brain, D_brain."""
        A, D, q = compute_q_A_D(Z, self.sigma_q_inv)
        return pd.DataFrame({
            "A_brain": (A - self.A_mean_cal) / self.A_std_cal,
            "D_brain": (D - self.D_mean_cal) / self.D_std_cal,
            "D_raw": D,
        })


def build_geometry(mats, manifest, split, ages_by_idevent, fast=False):
    """Full Phase-A build: clocks on dev, bias+covariance+standardization on cal.
    Returns (FrozenGeometry, per-partition scored DataFrame of A/D/z).
    OUTCOME-BLIND end to end."""
    man = manifest.set_index("id_event")
    man["partition"] = man["id"].map(split)
    ide = man.index

    # assemble aligned channel feature frames on the manifest index
    Xall = {ch: mats[ch].reindex(ide) for ch in CHANNELS}
    age = pd.Series(ages_by_idevent).reindex(ide)
    part = man["partition"]
    grp = man["id"]

    dev = part == "development"
    cal = part == "calibration"

    clocks, metrics = {}, {}
    for ch in CHANNELS:
        Xd, Xc = Xall[ch][dev.values], Xall[ch][cal.values]
        clk = train_channel_clock(ch, Xd, age[dev.values].to_numpy(),
                                  grp[dev.values].to_numpy(), Xc, age[cal.values].to_numpy(), fast=fast)
        clocks[ch] = clk
        metrics[ch] = {"heldout_r": clk.heldout_r, "cv_r_dev": clk.cv_r_dev,
                       "passed": clk.passed, "alpha": clk.alpha, "l1_ratio": clk.l1_ratio,
                       "n_features": len(clk.feature_names)}
    n_pass = sum(c.passed for c in clocks.values())

    # gaps for all rows using frozen clocks
    gaps = {ch: clock_predict(clocks[ch], Xall[ch]) - age.to_numpy() for ch in CHANNELS}
    # bias correction on calibration
    bias = {ch: fit_bias_correction(ch, gaps[ch][cal.values], age[cal.values].to_numpy())
            for ch in CHANNELS}
    Z = np.column_stack([apply_bias(bias[ch], gaps[ch], age.to_numpy()) for ch in CHANNELS])

    # Ledoit-Wolf covariance of q on CALIBRATION
    q_cal = Z[cal.values] @ HELMERT_C.T
    lw = LedoitWolf().fit(q_cal)
    sigma_q = lw.covariance_
    sigma_q_inv = np.linalg.pinv(sigma_q)
    A_cal, D_cal, _ = compute_q_A_D(Z[cal.values], sigma_q_inv)

    geom = FrozenGeometry(
        channels=CHANNELS, clocks=clocks, bias=bias, sigma_q=sigma_q, sigma_q_inv=sigma_q_inv,
        D_mean_cal=float(D_cal.mean()), D_std_cal=float(D_cal.std(ddof=1)),
        A_mean_cal=float(A_cal.mean()), A_std_cal=float(A_cal.std(ddof=1)),
        split_salt=SPLIT_SALT, clock_metrics=metrics, n_clocks_passed=n_pass,
    ).freeze()

    scored = geom.score(Z)
    scored.index = ide
    scored["partition"] = part.values
    scored["id"] = grp.values
    scored["event"] = man["event"].values
    scored["age"] = age.values
    for ch in CHANNELS:
        scored[f"z_{ch}"] = Z[:, CHANNELS.index(ch)]
    return geom, scored


# ----------------------------------------------------------------------
# Phase B — SEALED outcome analysis. Refuses to run without a frozen geometry.
# ----------------------------------------------------------------------
def _require_frozen(geom: FrozenGeometry):
    if not geom.frozen_hash or geom.frozen_hash != geom.compute_hash():
        raise RuntimeError("SEALED: geometry is not frozen/verified — outcome analysis blocked.")
    if geom.n_clocks_passed < MIN_CLOCKS_PASS:
        raise RuntimeError(f"STOP-RULE #10: only {geom.n_clocks_passed}/4 clocks passed "
                           f"(need >={MIN_CLOCKS_PASS}). A/D analysis aborted; report technical failure.")

def _nested_lrt(df, base_cols, test_col, y):
    """1-df nested test of adding test_col. OLS via numpy; F-test."""
    import numpy as np
    d = df.dropna(subset=base_cols + [test_col, y])
    Y = d[y].to_numpy(float)
    def fit(cols):
        X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in cols])
        beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
        resid = Y - X @ beta
        return beta, float(resid @ resid), X
    b0, rss0, _ = fit(base_cols)
    b1, rss1, X1 = fit(base_cols + [test_col])
    n, p1 = len(d), X1.shape[1]
    F = ((rss0 - rss1) / 1) / (rss1 / (n - p1))
    pval = float(stats.f.sf(F, 1, n - p1))
    # coefficient + CI for test_col (last)
    XtX_inv = np.linalg.pinv(X1.T @ X1)
    se = np.sqrt(rss1 / (n - p1) * np.diag(XtX_inv))
    beta_test = float(b1[-1]); se_test = float(se[-1])
    tcrit = stats.t.ppf(0.975, n - p1)
    return {"beta": beta_test, "se": se_test,
            "ci_low": beta_test - tcrit*se_test, "ci_high": beta_test + tcrit*se_test,
            "F": float(F), "p_value": pval, "n": int(n), "df_resid": int(n - p1)}

def _merge_scores_covariates(scored, covariates: pd.DataFrame):
    """Attach model covariates (indexed by id_event) to the scored A/D frame."""
    df = scored.copy()
    cov = covariates.reindex(df.index)
    for c in covariates.columns:
        df[c] = cov[c].values
    return df

def run_primary_longitudinal(geom, scored, outcomes, covariates,
                             gait_col="tlbx_walk_4_rawscore"):
    """SEALED longitudinal primary: annualized 4m gait-speed CHANGE ~ D + A + baseline + covs.
    Runs on calibration+final holdout participants with baseline all-4 + a later visit.
    NOTE gait raw = seconds to walk 4m (lower=faster); we convert to speed = 4/seconds
    so 'decline' is a DECREASE. outcomes indexed by id_event."""
    _require_frozen(geom)
    df = _merge_scores_covariates(scored, covariates)
    df = df[df["partition"].isin(["calibration", "final_test"])].copy()
    # gait -> speed (m/s); attach per visit
    g = outcomes[gait_col].reindex(df.index)
    df["gait_speed"] = 4.0 / g.replace(0, np.nan)
    order = {"V1":0,"V2":1,"V3":2,"V4":3}
    df["evord"] = df["event"].map(order).fillna(9)
    # baseline (earliest) and next visit per participant
    df = df.sort_values(["id","evord"])
    rows = []
    for pid, grp in df.groupby("id"):
        grp = grp.dropna(subset=["A_brain","D_brain"])
        base = grp[grp["evord"]==grp["evord"].min()]
        if base.empty: continue
        base = base.iloc[0]
        later = grp[grp["evord"]>base["evord"]]
        later = later.dropna(subset=["gait_speed"])
        if later.empty or pd.isna(base.get("gait_speed")): continue
        nxt = later.iloc[0]
        dt_years = (nxt["days_from_V1"]-base["days_from_V1"])/365.25 if "days_from_V1" in df else np.nan
        if not (dt_years and dt_years>0): continue
        rows.append({"id":pid, "d_gait_annual":(nxt["gait_speed"]-base["gait_speed"])/dt_years,
                     "D_brain":base["D_brain"], "A_brain":base["A_brain"],
                     "gait0":base["gait_speed"], "age":base["age"],
                     **{c:base[c] for c in covariates.columns if c in base and c!="days_from_V1"}})
    long_df = pd.DataFrame(rows)
    if len(long_df) < MIN_LONGITUDINAL_HOLDOUT:
        return {"status":"UNDERPOWERED","n":len(long_df),
                "threshold":MIN_LONGITUDINAL_HOLDOUT,
                "note":"longitudinal < threshold; cross-sectional promoted to primary"}
    covs = [c for c in ["A_brain","gait0","age","sex","education","site","height_inches","bmi"]
            if c in long_df.columns]
    res = _nested_lrt(long_df, covs, "D_brain", "d_gait_annual")
    res.update({"status":"RUN","design":"longitudinal","outcome":"annualized 4m gait-speed change",
                "n":len(long_df)})
    return res

def run_primary_crosssectional(geom, scored, outcomes, covariates,
                               gait_col="tlbx_walk_4_rawscore", partition="final_test"):
    """SEALED cross-sectional test: gait_speed ~ A + D + covs on final-test all-4."""
    _require_frozen(geom)
    df = _merge_scores_covariates(scored, covariates)
    df = df[df["partition"]==partition].copy()
    # one row per participant: baseline visit
    order = {"V1":0,"V2":1,"V3":2,"V4":3}
    df["evord"]=df["event"].map(order).fillna(9)
    df = df.sort_values(["id","evord"]).groupby("id").first().reset_index()
    g = outcomes[gait_col].reindex(pd.Index(df["id_event"] if "id_event" in df else df.index))
    df["gait_speed"] = (4.0/outcomes[gait_col].reindex(df.set_index("id").index).values) if False else 4.0/df.get("_g", np.nan)
    # robust: pull gait via id_event mapping
    ev = df["id"].astype(str) + "_" + df["event"].astype(str)
    df["gait_speed"] = 4.0/outcomes[gait_col].reindex(ev.values).values
    covs = [c for c in ["A_brain","age","sex","education","site","height_inches","bmi"] if c in df.columns]
    res = _nested_lrt(df, covs, "D_brain", "gait_speed")
    res.update({"status":"RUN","design":"cross_sectional","outcome":"4m gait speed","n":len(df.dropna(subset=['gait_speed','D_brain']))})
    return res

def run_secondaries(geom, scored, outcomes, covariates):
    """SEALED. Endurance/grip/cognition + LOCO D + raw SD/range. BH-FDR within family."""
    _require_frozen(geom)
    df = _merge_scores_covariates(scored, covariates)
    df = df[df["partition"].isin(["calibration","final_test"])].copy()
    ev = df["id"].astype(str) + "_" + df["event"].astype(str)
    out = []
    sec_map = {"endurance_2min":"tlbx_walk_2_rawscore",
               "grip_dominant":"tlbx_grip_dominant_score",
               "moca":"moca_sum"}
    covs = [c for c in ["A_brain","age","sex","education","site","height_inches","bmi"] if c in df.columns]
    for name, col in sec_map.items():
        if col not in outcomes.columns: continue
        d = df.copy(); d["y"] = outcomes[col].reindex(ev.values).values
        r = _nested_lrt(d, covs, "D_brain", "y")
        r["secondary"]=name; out.append(r)
    # BH-FDR
    if out:
        ps = np.array([o["p_value"] for o in out]); order=np.argsort(ps)
        m=len(ps); q=np.empty(m)
        for rank,idx in enumerate(order,1): q[idx]=ps[idx]*m/rank
        q=np.minimum.accumulate(q[order][::-1])[::-1]
        for i,idx in enumerate(order): out[idx]["q_value_bh"]=float(q[i])
    return out

def run_sensitivities(geom, scored, outcomes, covariates):
    """SEALED mandatory sensitivities: site-adjusted, raw SD/range vs D, leave-one-channel-out."""
    _require_frozen(geom)
    df = _merge_scores_covariates(scored, covariates)
    df = df[df["partition"].isin(["calibration","final_test"])].copy()
    ev = df["id"].astype(str)+"_"+df["event"].astype(str)
    df["gait_speed"]=4.0/outcomes["tlbx_walk_4_rawscore"].reindex(ev.values).values
    zc=[f"z_{c}" for c in CHANNELS]
    df["raw_sd"]=df[zc].std(axis=1); df["raw_range"]=df[zc].max(axis=1)-df[zc].min(axis=1)
    covs=[c for c in ["A_brain","age","sex","site","height_inches","bmi"] if c in df.columns]
    out=[]
    for label,tc in [("D_site_adj","D_brain"),("raw_sd_vs_D","raw_sd"),("raw_range_vs_D","raw_range")]:
        r=_nested_lrt(df,covs,tc,"gait_speed"); r["sensitivity"]=label; out.append(r)
    return out
