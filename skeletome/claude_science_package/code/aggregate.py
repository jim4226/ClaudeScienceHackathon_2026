#!/usr/bin/env python3
"""
SKELETOME — aggregation, permutation null, BH-FDR, and BLIND GDF5 validation.

Produces the final decision columns of the canonical TSV:
    composite_score, empirical_p, fdr_bh, candidate
and prints the BLIND GDF5 validation report (rank + predicted sign) WITHOUT
tuning anything on the controls.

COMPOSITE SCORE
  A single magnitude of predicted SKELETAL regulatory disruption, engine-agnostic
  so it works whether or not the optional ChromBPNet layer ran:
      skel_effect = max(|ag_dnase_delta|, |ag_atac_delta|,
                        |cbp_limb_logfc|, |cbp_msc_logfc|, |cbp_mg63_logfc|)  # NaNs ignored
      neural_penalty = |neural_delta|                                        # specificity
      composite_score = skel_effect - LAMBDA_NEURAL * neural_penalty
  LAMBDA_NEURAL rewards skeletal-SPECIFIC effects. Constraint / gBGC are applied
  as hard FILTERS in `candidate`, NOT folded into the score, so the score stays
  interpretable as "predicted skeletal accessibility disruption".

  candidate (LOCKED def, canonical): constrained AND NOT gbgc_flag AND skeletal effect.
      candidate = constrained & (~gbgc_flag) & (skel_effect >= SKEL_EFFECT_MIN)

PERMUTATION NULL — RECOMBINATION-MATCHED (LOCKED DECISION #2)
  gBGC tracks recombination rate, and recombination correlates with the very
  accessibility signals we score. A naive permutation would conflate the two.
  So the null is STRATIFIED by recombination rate: within recomb-rate bins we
  permute composite_score across substitutions, build a per-substitution null
  distribution, and compute a one-sided empirical p (fraction of matched-null
  draws >= observed). This asks: "is this substitution's skeletal effect larger
  than expected for OTHER substitutions at the SAME recombination rate?"

  empirical_p uses the (b+1)/(n+1) estimator (never 0). fdr_bh is Benjamini-
  Hochberg over all non-control substitutions via statsmodels.

BLIND GDF5 VALIDATION (LOCKED DECISION #4)
  Controls are tagged in `is_control`. Their expected effect DIRECTION is FROZEN
  here BEFORE looking at scores:
      GDF5-GROW1 : derived REDUCES accessibility  -> expect NEGATIVE delta
      GDF5-R4    : derived REDUCES accessibility  -> expect NEGATIVE delta
      HACNS1     : human-specific GAIN of function -> expect POSITIVE delta
      negative   : expect ~0 (|delta| small)
  We report, without tuning: each positive control's RANK by composite_score
  among all substitutions, and whether the observed sign matches the frozen
  expectation. This is genuine precision/recall (n>1), computed post-hoc.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

try:
    from statsmodels.stats.multitest import multipletests
    _HAVE_SM = True
except Exception:  # pragma: no cover
    _HAVE_SM = False

# ------------------------- tunables (documented) ----------------------------
LAMBDA_NEURAL = 0.5      # weight of neural specificity penalty in composite_score
SKEL_EFFECT_MIN = 0.10   # min skeletal effect magnitude to be candidate-eligible
N_PERMUTATIONS = 10000   # permutation-null draws
N_RECOMB_BINS = 10       # recombination-rate strata for the matched null
RNG_SEED = 20260707      # frozen seed for reproducibility

SKEL_EFFECT_COLS = ["ag_dnase_delta", "ag_atac_delta",
                    "cbp_limb_logfc", "cbp_msc_logfc", "cbp_mg63_logfc"]

# FROZEN control expectations (sign of derived-vs-ancestral accessibility delta).
# +1 expect increase, -1 expect decrease, 0 expect ~none.
CONTROL_EXPECTED_SIGN = {
    "GDF5-GROW1": -1,
    "GDF5-R4": -1,
    "HACNS1": +1,
    "negative": 0,
}


def compute_skel_effect(df: pd.DataFrame) -> pd.Series:
    present = [c for c in SKEL_EFFECT_COLS if c in df.columns]
    if not present:
        raise ValueError(f"No skeletal effect columns present; expected any of {SKEL_EFFECT_COLS}")
    mags = df[present].abs()
    # max over available engines, ignoring NaN; all-NaN row -> 0.
    return mags.max(axis=1).fillna(0.0)


def compute_composite(df: pd.DataFrame) -> pd.Series:
    skel = compute_skel_effect(df)
    neural = df["neural_delta"].abs().fillna(0.0) if "neural_delta" in df.columns else 0.0
    return skel - LAMBDA_NEURAL * neural


def recomb_matched_permutation(df: pd.DataFrame, score_col: str = "composite_score",
                               n_perm: int = N_PERMUTATIONS,
                               n_bins: int = N_RECOMB_BINS,
                               seed: int = RNG_SEED) -> np.ndarray:
    """
    One-sided empirical p per row, permuting composite_score WITHIN recomb-rate
    bins. Returns an array aligned to df.index.

    If recomb_rate_cMperMb is absent/all-NaN, degrades gracefully to a single
    unstratified bin (still a valid permutation null, just not recomb-matched)
    and notes the degradation via a stderr warning.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    obs = df[score_col].to_numpy(dtype=float)

    if "recomb_rate_cMperMb" in df.columns and df["recomb_rate_cMperMb"].notna().any():
        rr = pd.to_numeric(df["recomb_rate_cMperMb"], errors="coerce")
        # qcut into bins; NaN recomb -> its own bin so it is only compared to itself.
        try:
            bins = pd.qcut(rr.rank(method="first"), q=min(n_bins, max(1, rr.notna().sum())),
                           labels=False, duplicates="drop")
        except Exception:
            bins = pd.Series(np.zeros(n, dtype=int), index=df.index)
        bins = bins.fillna(-1).astype(int).to_numpy()
    else:
        print("[aggregate] WARNING: recomb_rate_cMperMb missing/empty — permutation "
              "null is UNSTRATIFIED (not recomb-matched). Fill P2 recomb rates for "
              "the headline matched null.", file=sys.stderr)
        bins = np.zeros(n, dtype=int)

    # Count, per row, how many matched-null permuted scores >= observed.
    ge_counts = np.zeros(n, dtype=np.int64)
    for b in np.unique(bins):
        idx = np.where(bins == b)[0]
        if len(idx) <= 1:
            # Singleton stratum: cannot permute meaningfully; assign neutral p later.
            ge_counts[idx] = -1  # sentinel
            continue
        block = obs[idx]
        for _ in range(n_perm):
            perm = rng.permutation(block)
            ge_counts[idx] += (perm >= block).astype(np.int64)

    emp_p = np.empty(n, dtype=float)
    for i in range(n):
        if ge_counts[i] < 0:
            emp_p[i] = 1.0  # singleton stratum -> conservative p=1
        else:
            emp_p[i] = (ge_counts[i] + 1) / (n_perm + 1)
    return emp_p


def benjamini_hochberg(pvals: np.ndarray) -> np.ndarray:
    if _HAVE_SM:
        _, q, _, _ = multipletests(pvals, method="fdr_bh")
        return q
    # Manual BH fallback.
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    q_sorted = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty(n)
    q[order] = np.clip(q_sorted, 0, 1)
    return q


def blind_gdf5_report(df: pd.DataFrame) -> dict:
    """
    Post-hoc, NO tuning. Ranks controls by composite_score and checks sign vs the
    FROZEN expectation. Returns a dict summary and prints a human-readable block.
    """
    if "is_control" not in df.columns:
        print("[blind] no is_control column — skipping GDF5 validation.", file=sys.stderr)
        return {}

    ranked = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    n_total = len(ranked)

    def observed_sign(r) -> int:
        # Use ATAC/DNase delta as the directional readout (accessibility).
        for c in ("ag_atac_delta", "ag_dnase_delta", "cbp_limb_logfc"):
            v = r.get(c, np.nan)
            if pd.notna(v) and abs(v) > 1e-9:
                return int(np.sign(v))
        return 0

    lines = ["", "==================== BLIND GDF5 / CONTROL VALIDATION ===================="]
    lines.append(f"(frozen expectations; ranks over all {n_total} substitutions by composite_score)")
    results = []
    tp = fp = 0
    for _, r in ranked.iterrows():
        ctrl = str(r.get("is_control", "none"))
        base = ctrl.split(":")[0].split("|")[0]  # normalize e.g. "GDF5-GROW1:..."
        if base not in CONTROL_EXPECTED_SIGN:
            continue
        exp = CONTROL_EXPECTED_SIGN[base]
        obs = observed_sign(r)
        if exp == 0:
            sign_ok = abs(float(r.get("ag_atac_delta", 0) or 0)) < SKEL_EFFECT_MIN
        else:
            sign_ok = (obs == exp)
        pct = 100.0 * r["rank"] / n_total
        results.append({
            "control": ctrl, "har_id": r.get("har_id"), "rank": int(r["rank"]),
            "percentile": round(pct, 2), "composite_score": round(float(r["composite_score"]), 4),
            "expected_sign": exp, "observed_sign": obs, "sign_match": bool(sign_ok),
        })
        if base != "negative":
            # positive controls: "recovered" if top-decile AND sign matches.
            recovered = sign_ok and pct <= 10.0
            tp += int(recovered)
            fp += int(not recovered)
        lines.append(
            f"  {ctrl:14s} {str(r.get('har_id','')):16s} rank={int(r['rank']):>4d}/"
            f"{n_total} ({pct:5.1f}%)  composite={float(r['composite_score']):+.4f}  "
            f"exp_sign={exp:+d} obs_sign={obs:+d}  sign_match={'YES' if sign_ok else 'no'}")

    n_pos = tp + fp
    precision_recall = (tp / n_pos) if n_pos else float("nan")
    lines.append(f"  ----")
    lines.append(f"  positive controls recovered (top-decile AND correct sign): "
                 f"{tp}/{n_pos}  (rate={precision_recall:.2f})")
    lines.append("=========================================================================")
    print("\n".join(lines))
    return {"controls": results, "positive_recovered": tp, "positive_total": n_pos,
            "recovery_rate": precision_recall}


def run(in_tsv: str, out_tsv: str, n_perm: int = N_PERMUTATIONS) -> pd.DataFrame:
    df = pd.read_csv(in_tsv, sep="\t", dtype={"chrom": str})

    # Ensure filter columns exist (may be produced upstream in P2/P5).
    for boolcol, default in (("constrained", False), ("gbgc_flag", False)):
        if boolcol not in df.columns:
            print(f"[aggregate] WARNING: '{boolcol}' missing — defaulting to {default}. "
                  f"candidate calls will be unreliable until P2 fills it.", file=sys.stderr)
            df[boolcol] = default

    df["composite_score"] = compute_composite(df)
    skel_effect = compute_skel_effect(df)

    # Permutation null over NON-control substitutions only (controls must not
    # inflate/deflate the genome-wide null). Controls get empirical_p=NaN.
    is_ctrl = df.get("is_control", pd.Series(["none"] * len(df))).astype(str).ne("none") & \
              df.get("is_control", pd.Series(["none"] * len(df))).astype(str).ne("")
    is_ctrl = is_ctrl & df.get("is_control", pd.Series(["none"] * len(df))).astype(str).ne("nan")

    df["empirical_p"] = np.nan
    df["fdr_bh"] = np.nan
    sub = df.loc[~is_ctrl].copy()
    if len(sub) >= 2:
        emp = recomb_matched_permutation(sub, "composite_score", n_perm=n_perm)
        df.loc[sub.index, "empirical_p"] = emp
        df.loc[sub.index, "fdr_bh"] = benjamini_hochberg(emp)
    else:
        print("[aggregate] fewer than 2 non-control rows — skipping null.", file=sys.stderr)

    # candidate = constrained AND NOT gbgc_flag AND skeletal effect (canonical).
    df["candidate"] = (df["constrained"].astype(bool)
                       & (~df["gbgc_flag"].astype(bool))
                       & (skel_effect >= SKEL_EFFECT_MIN))

    df.to_csv(out_tsv, sep="\t", index=False)
    print(f"[aggregate] wrote {out_tsv}: {int(df['candidate'].sum())} candidates, "
          f"{int((df['fdr_bh'] < 0.1).sum())} at FDR<0.1", file=sys.stderr)

    blind_gdf5_report(df)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description="Aggregate, permute, FDR, blind-validate.")
    ap.add_argument("--in", dest="in_tsv", required=True)
    ap.add_argument("--out", dest="out_tsv", required=True)
    ap.add_argument("--n-perm", type=int, default=N_PERMUTATIONS)
    args = ap.parse_args(argv)
    run(args.in_tsv, args.out_tsv, args.n_perm)


if __name__ == "__main__":
    main()
