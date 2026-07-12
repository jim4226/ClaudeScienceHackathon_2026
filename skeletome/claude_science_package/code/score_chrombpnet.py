#!/usr/bin/env python3
"""
SKELETOME — ChromBPNet variant scoring (OPTIONAL enrichment layer).

Gated behind an hour-1 smoke test (LOCKED DECISION #1). AlphaGenome is PRIMARY;
this module only ADDS the cbp_* columns when the heavy TF/ChromBPNet env is
available. It shells out to kundajelab/variant-scorer against the ENCODE skeletal
models and merges logFC + JSD back into the canonical TSV.

INTERFACE VERIFICATION (2026-07, github.com/kundajelab/variant-scorer):
  python src/variant_scoring.py \
      --list      <variants.tsv> \
      --genome    <hg38.fa> \
      --model     <chrombpnet_nobias.h5> \
      --out_prefix <prefix> \
      --chrom_sizes <hg38.chrom.sizes> \
      [--schema chrombpnet]
  Input "chrombpnet" schema columns (1-indexed pos):  chr  pos  allele1  allele2  variant_id
  Output <prefix>.variant_scores.tsv columns include:  logfc  jsd  abs_logfc  ...
    logfc = log2 fold-change total predicted coverage allele2 vs allele1
    jsd   = Jensen-Shannon distance between bias-corrected base-res profiles
  => We set allele1 = ref_ancestral, allele2 = alt_human, so logfc is
     derived-vs-ancestral (same sign convention as AlphaGenome).

ENCODE MODELS (LOCKED locators):
  limb  : ENCSR138OCE / ENCSR858EVI   -> cbp_limb_logfc
  MSC   : ENCFF640AVL.tar.gz          -> cbp_msc_logfc     (H1-MSC)
  MG63  : ENCFF841SWM.tar.gz          -> cbp_mg63_logfc    (MG63 osteosarcoma)
  Each tarball contains a chrombpnet_nobias.h5 (bias-corrected) model. The
  variant-scorer uses the bias-corrected model directly; the raw bias model is
  only needed for training, not for --model scoring. jsd is reported once (we
  store the limb-model JSD as cbp_jsd; per-model JSDs go into notes).

ISOLATED-ENV INSTALL (do NOT mix with the AlphaGenome env):
  # Option 1 — Docker (preferred):
  docker run --rm -v $PWD:/work kundajelab/chrombpnet:latest \
      python /variant-scorer/src/variant_scoring.py ...
  # Option 2 — conda:
  conda create -n cbp python=3.10 -y && conda activate cbp
  pip install tensorflow==2.11 chrombpnet
  git clone https://github.com/kundajelab/variant-scorer

This module is IMPORT-SAFE with none of that installed: it only checks for the
model files + scorer script at call time and no-ops (leaving cbp_* as NaN) when
they are absent, so the pipeline never hard-fails on the optional layer.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

# Model registry: logical name -> (env var for model .h5 path, output column).
CBP_MODELS = {
    "limb": ("SKELETOME_CBP_LIMB_H5", "cbp_limb_logfc"),   # ENCSR138OCE/ENCSR858EVI
    "msc":  ("SKELETOME_CBP_MSC_H5",  "cbp_msc_logfc"),    # ENCFF640AVL
    "mg63": ("SKELETOME_CBP_MG63_H5", "cbp_mg63_logfc"),   # ENCFF841SWM
}
CBP_COLUMNS = [c for (_, c) in CBP_MODELS.values()] + ["cbp_jsd"]


def _write_variant_list(df: pd.DataFrame, path: str) -> None:
    """chrombpnet schema: chr pos allele1 allele2 variant_id (1-indexed pos)."""
    out = pd.DataFrame({
        "chr": df["chrom"].astype(str),
        "pos": df["pos_hg38"].astype(int),
        "allele1": df["ref_ancestral"].astype(str).str.upper(),  # ancestral/REF
        "allele2": df["alt_human"].astype(str).str.upper(),      # derived/ALT
        "variant_id": df["har_id"].astype(str) + ":" + df["pos_hg38"].astype(str),
    })
    out.to_csv(path, sep="\t", index=False, header=False)


def _run_scorer(scorer_py: str, var_list: str, genome_fa: str, model_h5: str,
                chrom_sizes: str, out_prefix: str) -> pd.DataFrame | None:
    cmd = [
        sys.executable, scorer_py,
        "--list", var_list,
        "--genome", genome_fa,
        "--model", model_h5,
        "--chrom_sizes", chrom_sizes,
        "--out_prefix", out_prefix,
        "--schema", "chrombpnet",
    ]
    print(f"[chrombpnet] {' '.join(cmd)}", file=sys.stderr)
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[chrombpnet] scorer failed: {e}", file=sys.stderr)
        return None
    scores_path = f"{out_prefix}.variant_scores.tsv"
    if not os.path.exists(scores_path):
        print(f"[chrombpnet] expected output missing: {scores_path}", file=sys.stderr)
        return None
    return pd.read_csv(scores_path, sep="\t")


def run(in_tsv: str, out_tsv: str, genome_fa: str | None, chrom_sizes: str | None,
        scorer_py: str | None, models: list[str]) -> pd.DataFrame:
    df = pd.read_csv(in_tsv, sep="\t", dtype={"chrom": str})
    for col in CBP_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    if "notes" not in df.columns:
        df["notes"] = ""

    # Preconditions for the optional layer. If unmet, no-op cleanly.
    scorer_py = scorer_py or os.environ.get("SKELETOME_VARIANT_SCORER")
    genome_fa = genome_fa or os.environ.get("SKELETOME_HG38_FA")
    chrom_sizes = chrom_sizes or os.environ.get("SKELETOME_HG38_CHROMSIZES")
    if not (scorer_py and genome_fa and chrom_sizes
            and os.path.exists(scorer_py) and os.path.exists(genome_fa)
            and os.path.exists(chrom_sizes)):
        print("[chrombpnet] SKIPPED — variant-scorer / genome / chrom_sizes not "
              "all present. cbp_* left as NaN (AlphaGenome is primary). Set "
              "SKELETOME_VARIANT_SCORER, SKELETOME_HG38_FA, SKELETOME_HG38_CHROMSIZES "
              "and the per-model H5 env vars to enable.", file=sys.stderr)
        df.to_csv(out_tsv, sep="\t", index=False)
        return df

    tmpdir = tempfile.mkdtemp(prefix="skeletome_cbp_")
    var_list = os.path.join(tmpdir, "variants.tsv")
    _write_variant_list(df, var_list)
    vid = df["har_id"].astype(str) + ":" + df["pos_hg38"].astype(str)
    df["_vid"] = vid.values

    for name in models:
        if name not in CBP_MODELS:
            print(f"[chrombpnet] unknown model '{name}', skipping.", file=sys.stderr)
            continue
        env_var, col = CBP_MODELS[name]
        model_h5 = os.environ.get(env_var)
        if not (model_h5 and os.path.exists(model_h5)):
            print(f"[chrombpnet] {name}: {env_var} unset/missing -> {col} stays NaN.",
                  file=sys.stderr)
            continue
        out_prefix = os.path.join(tmpdir, name)
        scores = _run_scorer(scorer_py, var_list, genome_fa, model_h5,
                             chrom_sizes, out_prefix)
        if scores is None:
            continue
        # Map by variant_id. Column names verified: logfc, jsd (+ variant_id).
        vid_col = "variant_id" if "variant_id" in scores.columns else scores.columns[0]
        lfc = dict(zip(scores[vid_col].astype(str), pd.to_numeric(scores.get("logfc"), errors="coerce")))
        df[col] = df["_vid"].map(lfc)
        if name == "limb" and "jsd" in scores.columns:
            jmap = dict(zip(scores[vid_col].astype(str),
                            pd.to_numeric(scores["jsd"], errors="coerce")))
            df["cbp_jsd"] = df["_vid"].map(jmap)
        print(f"[chrombpnet] merged {name} -> {col} "
              f"({df[col].notna().sum()} non-NaN)", file=sys.stderr)

    df.drop(columns=["_vid"], inplace=True, errors="ignore")
    df.to_csv(out_tsv, sep="\t", index=False)
    print(f"[chrombpnet] wrote {out_tsv}", file=sys.stderr)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(description="Optional ChromBPNet variant scoring.")
    ap.add_argument("--in", dest="in_tsv", required=True)
    ap.add_argument("--out", dest="out_tsv", required=True)
    ap.add_argument("--genome", default=None, help="hg38 FASTA (or SKELETOME_HG38_FA)")
    ap.add_argument("--chrom-sizes", default=None, help="hg38 chrom.sizes (or SKELETOME_HG38_CHROMSIZES)")
    ap.add_argument("--scorer", default=None,
                    help="path to variant_scoring.py (or SKELETOME_VARIANT_SCORER)")
    ap.add_argument("--models", default="limb,msc,mg63",
                    help="comma list from {limb,msc,mg63}")
    args = ap.parse_args(argv)
    run(args.in_tsv, args.out_tsv, args.genome, args.chrom_sizes, args.scorer,
        [m.strip() for m in args.models.split(",") if m.strip()])


if __name__ == "__main__":
    main()
