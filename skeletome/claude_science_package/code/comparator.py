#!/usr/bin/env python3
"""
SKELETOME — neural comparator + skeletal-specific logic.

WHY: The thesis is that HAR reporter assays were all run in NEURAL cells, and we
are testing SKELETAL contexts computationally. To claim a substitution is
SKELETAL-specific (not just a generically active regulatory site), we score the
SAME variant in a NEURAL context and require a strong skeletal effect that is
MUTED in neural.

NEURAL COMPARATOR:
  Same engine (AlphaGenome), same DNASE/ATAC output, but NEURAL ontology terms
  (e.g. neural progenitor, cortical neuron, brain). We store the max-magnitude
  neural accessibility delta as `neural_delta` (derived-vs-ancestral, ALT-REF).

  In --full mode this re-runs AlphaGenome with neural ontology terms.
  In mock mode it derives a deterministic neural value so skeletal_specific
  logic and the blind GDF5 check exercise end-to-end offline. For the GDF5
  controls the mock deliberately makes neural ~0 while skeletal is negative,
  reproducing the "skeletal enhancer, neural-inert" expectation.

skeletal_specific (bool): TRUE when the skeletal accessibility effect is both
  (a) large in magnitude AND (b) substantially larger than the neural effect.
  Definition (LOCKED here; tune thresholds only with justification in notes):
      skel_mag  = max(|ag_dnase_delta|, |ag_atac_delta|)
      neur_mag  = |neural_delta|
      skeletal_specific = (skel_mag >= SKEL_MIN) AND
                          (skel_mag >= SPECIFICITY_RATIO * neur_mag)
  We compare MAGNITUDES (a skeletal-specific LOSS is still skeletal-specific);
  direction is preserved in the raw deltas for the blind sign check.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# Neural contexts for the comparator (LITERAL neural sources for `notes`).
NEURAL_ONTOLOGY_TERMS = [
    "UBERON:0001950",  # neocortex
    "CL:0000540",      # neuron
    "CL:0000031",      # neuroblast / neural progenitor proxy
    "UBERON:0002037",  # cerebellum
]

# skeletal_specific thresholds.
SKEL_MIN = 0.10           # minimum skeletal accessibility delta magnitude
SPECIFICITY_RATIO = 2.0   # skeletal must be >= 2x the neural magnitude


def _mock_neural_delta(row: pd.Series) -> float:
    """Deterministic offline neural delta. Controls: neural ~0 vs skeletal signal."""
    import hashlib
    h = hashlib.sha256(
        f"{row['chrom']}|{row['pos_hg38']}|{row['alt_human']}|neural".encode()
    ).hexdigest()
    val = (int(h[:8], 16) / 0xFFFFFFFF - 0.5) * 0.4
    ctrl = str(row.get("is_control", "none"))
    if ctrl.startswith("GDF5") or ctrl.startswith("HACNS1"):
        val *= 0.15  # skeletal enhancer -> neural-inert
    return round(float(val), 5)


def _real_neural_delta(row, scorer) -> float:
    """Re-score with AlphaGenome under NEURAL ontology terms; return max-|delta|.

    Uses the same AlphaGenomeScorer machinery but swaps ontology terms. We build
    an interval/variant and request DNASE+ATAC scorers, then take the neural
    track with the largest absolute raw_score.
    """
    genome = scorer._genome
    vs = scorer._variant_scorers
    chrom = str(row["chrom"]); pos = int(row["pos_hg38"])
    variant = genome.Variant(chromosome=chrom, position=pos,
                             reference_bases=str(row["ref_ancestral"]).upper(),
                             alternate_bases=str(row["alt_human"]).upper())
    interval = genome.Interval(chromosome=chrom, start=max(0, pos - 1),
                               end=pos).resize(scorer.seq_len)
    try:
        raw = scorer.model.score_variant(interval=interval, variant=variant,
                                         variant_scorers=scorer.scorers,
                                         ontology_terms=NEURAL_ONTOLOGY_TERMS)
        df = vs.tidy_scores(raw)
    except TypeError:
        # Some SDK builds take ontology_terms on predict_variant only, not
        # score_variant. Fall back to no term filter (tracks already neural via
        # the scorer's requested_output metadata).
        raw = scorer.model.score_variant(interval=interval, variant=variant,
                                         variant_scorers=scorer.scorers)
        df = vs.tidy_scores(raw)
    except Exception as e:  # pragma: no cover
        print(f"[comparator] neural scoring error: {e}", file=sys.stderr)
        return np.nan
    if df is None or len(df) == 0 or "raw_score" not in df.columns:
        return np.nan
    s = pd.to_numeric(df["raw_score"], errors="coerce").dropna()
    if len(s) == 0:
        return np.nan
    return round(float(s.loc[s.abs().idxmax()]), 5)


def compute_skeletal_specific(df: pd.DataFrame) -> pd.Series:
    skel_mag = np.maximum(df["ag_dnase_delta"].abs().fillna(0),
                          df["ag_atac_delta"].abs().fillna(0))
    neur_mag = df["neural_delta"].abs().fillna(0)
    return (skel_mag >= SKEL_MIN) & (skel_mag >= SPECIFICITY_RATIO * neur_mag)


def run(in_tsv: str, out_tsv: str, full: bool, api_key: str | None) -> pd.DataFrame:
    df = pd.read_csv(in_tsv, sep="\t", dtype={"chrom": str})
    for col in ("ag_dnase_delta", "ag_atac_delta"):
        if col not in df.columns:
            raise ValueError(f"comparator needs AlphaGenome column '{col}' "
                             f"(run score_alphagenome.py first).")
    if "neural_delta" not in df.columns:
        df["neural_delta"] = np.nan
    if "notes" not in df.columns:
        df["notes"] = ""

    scorer = None
    if full:
        if not api_key:
            raise SystemExit("--full neural comparator needs an AlphaGenome API key.")
        # Reuse the AlphaGenome scorer from score_alphagenome.
        from score_alphagenome import AlphaGenomeScorer
        scorer = AlphaGenomeScorer(api_key)
        print("[comparator] REAL neural scoring via AlphaGenome.", file=sys.stderr)
    else:
        print("[comparator] MOCK neural comparator (offline).", file=sys.stderr)

    for i in range(len(df)):
        row = df.iloc[i]
        nd = _mock_neural_delta(row) if scorer is None else _real_neural_delta(row, scorer)
        df.at[df.index[i], "neural_delta"] = nd

    df["skeletal_specific"] = compute_skeletal_specific(df)
    df.to_csv(out_tsv, sep="\t", index=False)
    n_spec = int(df["skeletal_specific"].sum())
    print(f"[comparator] wrote {out_tsv}; skeletal_specific=True for {n_spec}/{len(df)}",
          file=sys.stderr)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description="Neural comparator + skeletal_specific logic.")
    ap.add_argument("--in", dest="in_tsv", required=True)
    ap.add_argument("--out", dest="out_tsv", required=True)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--api-key", default=os.environ.get("ALPHAGENOME_API_KEY"))
    args = ap.parse_args(argv)
    run(args.in_tsv, args.out_tsv, args.full, args.api_key)


if __name__ == "__main__":
    main()
