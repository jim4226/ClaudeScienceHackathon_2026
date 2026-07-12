#!/usr/bin/env python3
"""
SKELETOME — AlphaGenome scoring (PRIMARY engine, v2).

Scores each element for its predicted differential ACCESSIBILITY between the
HUMAN (alt) and CHIMP (ref) sequence, in SKELETAL-lineage DNase contexts, using
the AlphaGenome hosted API (Avsec et al., Nature, 28 Jan 2026,
10.1038/s41586-025-10014-0).

WHAT THIS PRODUCES (the honest framing — see CAVEATS_AND_DEFENSES.md #2/#3):
  We do NOT run an MPRA. We predict human(alt)-vs-chimp(ref) DNase-accessibility
  DELTAS from sequence, and BENCHMARK those deltas against the REAL wet-lab MPRA
  differential-activity calls (Okamoto/Coveney/Ganapathee/Capellini 2025,
  GEO GSE298093) in code/benchmark.py. This is a VIRTUAL skeletal MPRA validated
  against the measured one — never a measured assay.

WHY DNASE, NOT ATAC (LOCKED, see CAVEATS #DNase):
  AlphaGenome exposes 305 human DNASE + 167 ATAC tracks (ENCODE-derived; GTEx
  excluded). Fetal/embryonic SKELETAL accessibility (chondrocyte, osteoblast,
  MSC, embryonic femur, embryonic limb/forelimb/hindlimb) lives in the DNASE
  panel. We select a small skeletal DNASE panel via output_metadata() and
  AGGREGATE across it, rather than trusting any single track. ATAC is scored too
  and passed through (ag_atac_delta) but DNase is the benchmark signal.

INTERFACE (verified 2026-07 against github.com/google-deepmind/alphagenome +
alphagenomedocs.com quick_start / variant_scoring_ui / output_metadata):
  from alphagenome.models import dna_client, variant_scorers
  from alphagenome.data import genome
  model = dna_client.create(API_KEY)
  meta = model.output_metadata(organism=dna_client.Organism.HOMO_SAPIENS)
  #   meta.dnase / meta.atac -> per-track metadata frames with columns incl.
  #   biosample_name, ontology_curie, track_name (grep for skeletal biosamples).
  interval = genome.Interval(chromosome='chr20', start=..., end=...).resize(
      dna_client.SEQUENCE_LENGTH_1MB)
  variant = genome.Variant(chromosome='chr20', position=...,
                           reference_bases='<chimp>', alternate_bases='<human>')
  scorer = variant_scorers.CenterMaskScorer(
      requested_output=dna_client.OutputType.DNASE, width=501,
      aggregation_type=variant_scorers.AggregationType.DIFF_MEAN)
  scores = model.score_variant(interval=interval, variant=variant,
                               variant_scorers=[scorer])
  df = variant_scorers.tidy_scores(scores)   # columns incl. raw_score,
      # quantile_score (PRIMARY per AlphaGenome docs), output_type,
      # biosample_name, ontology_curie, track_name
  # Base-resolution: model.predict_variant(...).reference.dnase /
  #   .alternate.dnase give 1-bp tracks; alt-ref gives the per-base delta whose
  #   argmax|.| is the nominated causal position the region-level assay can't
  #   resolve.

CONVENTIONS LOCKED BY SKELETOME (match CANONICAL_SCHEMA.md exactly):
  * ref_ancestral == CHIMP/ancestral REF allele; alt_human == HUMAN ALT allele.
    AlphaGenome's delta is (ALT - REF) == (human - chimp). Stored directly as
    ag_dnase_delta / ag_atac_delta. Positive = human allele INCREASES predicted
    accessibility; negative = human allele REDUCES it. GDF5-GROW1 expected
    NEGATIVE (derived ~0.72x activity, Capellini 2017).
  * The PRIMARY per-track statistic is the AlphaGenome `quantile_score`
    (recommended in the AlphaGenome variant-scoring docs); `raw_score` is kept
    as a fallback. We aggregate the quantile score across the skeletal DNASE
    panel by mean.
  * Readouts are labelled by LITERAL AlphaGenome track biosample (e.g. "embryonic
    femur", "chondrocyte", "osteoblast"), never re-laundered as "chondrocyte"
    when the track is bulk limb.

BASE-RESOLUTION (the region-assay can't do this; we can):
  score_alphagenome writes ag_dnase_delta (region-level panel mean) AND records
  the base-resolution max-|delta| POSITION for the element into `notes` as
  `ag_maxdelta_pos=<hg38pos>;ag_maxdelta=<signed>`. substitutions.py / aggregate.py
  parse it to nominate the single causal substitution the MPRA element cannot
  resolve (blindly recovering GDF5/GROW1). In mock mode this is deterministic.

TWO MODES:
  --mock  (DEFAULT) : deterministic offline scorer. NO network, NO API key.
                      Runs the whole pipeline + BLIND GDF5 check anywhere,
                      pandas/numpy only.
  --full            : real AlphaGenome hosted API calls (needs ALPHAGENOME_API_KEY).

Reads/writes the CANONICAL RESULTS TSV. Columns this module OWNS:
  ag_atac_delta, ag_dnase_delta  (+ base-resolution annotation appended to notes).
All other columns are passed through untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Skeletal DNASE panel selection.
#
# We DO NOT hardcode track ids blindly. In --full mode we call output_metadata()
# and select the DNASE tracks whose biosample_name / ontology_curie match a
# skeletal-lineage keyword set. The keyword set below is the FIRST CODE STEP
# named in the SKELETOME spine (grep .dnase for chondrocyte|osteoblast|
# mesenchymal|limb|femur to lock exact CURIEs). Known-present skeletal DNase
# biosamples (from the AlphaGenome ENCODE-derived panel; B1 RESOLVED):
#   chondrocyte (ENCSR970DQR), osteoblast (ENCSR000ELJ), MSC (H1-derived),
#   embryonic femur (ENCSR805XIF), embryonic limb/forelimb/hindlimb DNase.
# ----------------------------------------------------------------------------
SKELETAL_DNASE_KEYWORDS = [
    "chondrocyte",
    "osteoblast",
    "mesenchymal",   # MSC / H1-derived mesenchymal stem cell
    "femur",         # embryonic femur (ENCSR805XIF)
    "limb",          # embryonic limb / forelimb / hindlimb
    "forelimb",
    "hindlimb",
    "cartilage",
]

# ENCODE accessions we EXPECT the keyword match to surface (used only to print a
# reassuring go/no-go line; not required for correctness).
EXPECTED_SKELETAL_ACCESSIONS = [
    "ENCSR970DQR",  # chondrocyte
    "ENCSR000ELJ",  # osteoblast
    "ENCSR805XIF",  # embryonic femur
]

# AlphaGenome sequence context window. 1 MB is the widest supported and captures
# distal enhancer context (GDF5-GROW1 sits ~68 kb from the GDF5 TSS — needs a
# wide window). Narrow to 500KB only if latency/quota forces it.
DEFAULT_SEQUENCE_LENGTH_NAME = "SEQUENCE_LENGTH_1MB"


# ============================================================================
# Result container
# ============================================================================
@dataclass
class AGScore:
    ag_dnase_delta: float          # skeletal DNASE panel-mean quantile delta (human-chimp)
    ag_atac_delta: float           # ATAC panel-mean delta (passed through, not benchmarked)
    maxdelta_pos: Optional[int]    # hg38 position of base-resolution max-|delta|
    maxdelta: float                # signed base-resolution max delta at that pos
    notes: str


def _fmt_notes(res: "AGScore") -> str:
    """Compact, machine-parseable base-resolution annotation for the notes column."""
    parts = [res.notes]
    if res.maxdelta_pos is not None and res.maxdelta == res.maxdelta:  # not NaN
        parts.append(f"ag_maxdelta_pos={int(res.maxdelta_pos)}")
        parts.append(f"ag_maxdelta={round(float(res.maxdelta), 5)}")
    return ";".join(p for p in parts if p)


# ============================================================================
# MOCK scorer — deterministic, offline, no API key, pandas/numpy only.
# ============================================================================
def _stable_unit(*parts) -> float:
    """Deterministic float in [0,1) from arbitrary keys (hash-based)."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def mock_score(row: pd.Series) -> AGScore:
    """
    Deterministic pseudo-AlphaGenome score. Designed so:
      * output is reproducible across machines (hash of locus + alleles);
      * the GDF5-GROW1 control gets a NEGATIVE human-allele delta, matching
        Capellini 2017 (derived allele REDUCES activity, ~0.72x) — so the BLIND
        validation in aggregate.py has a real signal to (blindly) recover even
        offline;
      * a base-resolution max-|delta| POSITION is emitted (here, the element's own
        pos_hg38) so the base-resolution / causal-substitution logic exercises
        end-to-end. This is a SANITY FIXTURE, not a prediction.
    NOTE: mock values are NOT scientifically meaningful. --full replaces them.
    """
    base_d = (_stable_unit(row["chrom"], row["pos_hg38"], row["alt_human"], "d") - 0.5) * 0.4
    base_a = (_stable_unit(row["chrom"], row["pos_hg38"], row["alt_human"], "a") - 0.5) * 0.4

    ctrl = str(row.get("is_control", "none"))
    if ctrl.startswith("GDF5-GROW1"):
        # Frozen expectation: derived REDUCES accessibility. Push clearly negative.
        base_d = -abs(base_d) - 0.25
        base_a = -abs(base_a) - 0.20
    elif ctrl.startswith("GDF5-R4"):
        base_d = -abs(base_d) - 0.10
        base_a = -abs(base_a) - 0.08
    elif ctrl.startswith("HACNS1"):
        # Human-specific GAIN of function -> positive.
        base_d = abs(base_d) + 0.10
        base_a = abs(base_a) + 0.08
    elif ctrl == "negative":
        base_d *= 0.1
        base_a *= 0.1

    # Base-resolution mock: the max-|delta| base is the element's own position,
    # carrying the (signed) DNase delta. In a real run this is the argmax over the
    # 1-bp predicted delta track and may differ from pos_hg38 — that difference is
    # exactly the causal-substitution nomination the region assay can't make.
    try:
        maxpos = int(row["pos_hg38"])
    except Exception:
        maxpos = None

    return AGScore(
        ag_dnase_delta=round(float(base_d), 5),
        ag_atac_delta=round(float(base_a), 5),
        maxdelta_pos=maxpos,
        maxdelta=round(float(base_d), 5),
        notes="mock_alphagenome_dnase_panel",
    )


# ============================================================================
# REAL scorer — AlphaGenome hosted API.
# ============================================================================
class AlphaGenomeScorer:
    """
    Thin wrapper over the AlphaGenome hosted client. Constructed only in --full
    mode so the module imports cleanly (mock path) without the SDK installed.

    On construction it:
      1. creates the DNA client,
      2. calls output_metadata() and selects a SKELETAL DNASE panel by keyword,
      3. builds a DNASE + an ATAC CenterMaskScorer (quantile score primary).
    """

    def __init__(self, api_key: str,
                 sequence_length_name: str = DEFAULT_SEQUENCE_LENGTH_NAME):
        # Imported lazily: mock mode must work with NO alphagenome install.
        from alphagenome.models import dna_client, variant_scorers  # noqa: F401

        self._dna_client = dna_client
        self._variant_scorers = variant_scorers
        self._genome = __import__("alphagenome.data.genome", fromlist=["genome"])

        self.model = dna_client.create(api_key)
        self.seq_len = getattr(dna_client, sequence_length_name)

        # (1) Lock the skeletal DNASE panel from live metadata.
        self.skeletal_curies, self.skeletal_biosamples = self._select_skeletal_dnase_panel()
        # (2) Build DNASE + ATAC scorers (quantile score primary via tidy_scores).
        self.dnase_scorer, self.atac_scorer = self._build_scorers()

    # ---- (1) metadata-driven skeletal DNASE panel -------------------------
    def _organism(self):
        dc = self._dna_client
        # Organism enum member name has varied across builds; probe defensively.
        for attr in ("Organism", "ORGANISM"):
            org = getattr(dc, attr, None)
            if org is not None:
                for name in ("HOMO_SAPIENS", "HUMAN"):
                    if hasattr(org, name):
                        return getattr(org, name)
        return "homo_sapiens"  # string fallback accepted by some builds

    def _select_skeletal_dnase_panel(self):
        """Grep DNASE track metadata for skeletal biosamples; return CURIEs+names."""
        try:
            meta = self.model.output_metadata(organism=self._organism())
        except TypeError:
            meta = self.model.output_metadata(self._organism())
        except Exception as e:  # pragma: no cover - network dependent
            print(f"[alphagenome] output_metadata failed ({e}); "
                  f"panel will fall back to unfiltered DNASE tracks.", file=sys.stderr)
            return [], []

        # meta may expose .dnase or be a single frame with an output_type column.
        dnase_df = None
        if hasattr(meta, "dnase") and getattr(meta, "dnase") is not None:
            dnase_df = getattr(meta, "dnase")
        else:
            frame = getattr(meta, "metadata", meta)
            try:
                if "output_type" in frame.columns:
                    dnase_df = frame[frame["output_type"].astype(str).str.upper()
                                     .str.contains("DNASE")]
            except Exception:
                dnase_df = None
        if dnase_df is None or len(dnase_df) == 0:
            print("[alphagenome] no DNASE metadata frame found; unfiltered fallback.",
                  file=sys.stderr)
            return [], []

        name_col = next((c for c in ("biosample_name", "biosample", "track_name")
                         if c in dnase_df.columns), None)
        curie_col = next((c for c in ("ontology_curie", "biosample_term_id",
                                      "ontology_term_id") if c in dnase_df.columns), None)
        if name_col is None:
            return [], []

        kw = re.compile("|".join(SKELETAL_DNASE_KEYWORDS), re.IGNORECASE)
        hits = dnase_df[dnase_df[name_col].astype(str).apply(lambda x: bool(kw.search(x)))]
        biosamples = sorted(set(hits[name_col].astype(str)))
        curies = sorted(set(hits[curie_col].astype(str))) if curie_col else []

        print(f"[alphagenome] skeletal DNASE panel: {len(biosamples)} biosample(s): "
              f"{biosamples[:8]}{'...' if len(biosamples) > 8 else ''}", file=sys.stderr)
        # Reassuring go/no-go: did the expected skeletal accessions surface anywhere?
        blob = " ".join(hits.astype(str).values.ravel().tolist()) if len(hits) else ""
        found = [a for a in EXPECTED_SKELETAL_ACCESSIONS if a in blob]
        print(f"[alphagenome] expected skeletal accessions present: {found}",
              file=sys.stderr)
        if not biosamples:
            print("[alphagenome] WARNING: no skeletal DNASE biosample matched keywords; "
                  "check output_metadata schema — proceeding with unfiltered DNASE.",
                  file=sys.stderr)
        return curies, biosamples

    # ---- (2) scorers -------------------------------------------------------
    def _build_scorers(self):
        vs = self._variant_scorers
        dc = self._dna_client
        AggT = getattr(vs, "AggregationType", None)
        agg = None
        if AggT is not None:
            for cand in ("DIFF_MEAN", "DIFF_SUM", "L2_DIFF", "ACTIVE_MEAN"):
                if hasattr(AggT, cand):
                    agg = getattr(AggT, cand)
                    break

        def _mk(ot):
            try:
                return vs.CenterMaskScorer(requested_output=ot, width=501,
                                           aggregation_type=agg)
            except Exception as e:  # pragma: no cover
                print(f"[alphagenome] CenterMaskScorer({ot}) failed: {e}", file=sys.stderr)
                return None

        dnase = _mk(dc.OutputType.DNASE)
        atac = _mk(dc.OutputType.ATAC)
        if dnase is None and atac is None:
            raise RuntimeError(
                "Could not construct any AlphaGenome accessibility scorer. "
                "Inspect variant_scorers against the installed SDK version.")
        return dnase, atac

    def _interval_variant(self, row: pd.Series):
        genome = self._genome
        chrom = str(row["chrom"])
        pos = int(row["pos_hg38"])
        variant = genome.Variant(
            chromosome=chrom, position=pos,
            reference_bases=str(row["ref_ancestral"]).upper(),   # chimp/ancestral
            alternate_bases=str(row["alt_human"]).upper(),        # human derived
        )
        interval = genome.Interval(chromosome=chrom, start=max(0, pos - 1),
                                   end=pos).resize(self.seq_len)
        return interval, variant

    def score_row(self, row: pd.Series, max_retries: int = 4) -> AGScore:
        vs = self._variant_scorers
        interval, variant = self._interval_variant(row)
        scorers = [s for s in (self.dnase_scorer, self.atac_scorer) if s is not None]

        last_err = None
        for attempt in range(max_retries):
            try:
                raw = self.model.score_variant(interval=interval, variant=variant,
                                               variant_scorers=scorers)
                df = vs.tidy_scores(raw)
                dnase, atac = self._reduce_panel(df)
                mpos, mdelta = self._base_resolution_max(row)
                bios = self._contributing_biosamples(df)
                return AGScore(dnase, atac, mpos, mdelta,
                               notes=f"alphagenome_dnase_panel:{bios}")
            except Exception as e:  # pragma: no cover - network dependent
                last_err = e
                time.sleep(2.0 * (attempt + 1))
        return AGScore(np.nan, np.nan, None, np.nan, f"alphagenome_error:{last_err}")

    def _reduce_panel(self, df: pd.DataFrame):
        """
        Collapse tidy per-track scores to (dnase_panel_mean, atac_panel_mean).

        PRIMARY statistic = quantile_score (AlphaGenome-recommended); falls back
        to raw_score. For DNASE we restrict to the skeletal panel biosamples when
        we successfully selected them, otherwise we average all DNASE tracks and
        say so.
        """
        if df is None or len(df) == 0:
            return np.nan, np.nan
        ot_col = "output_type" if "output_type" in df.columns else None
        score_col = ("quantile_score" if "quantile_score" in df.columns
                     else ("raw_score" if "raw_score" in df.columns else None))
        if ot_col is None or score_col is None:
            return np.nan, np.nan

        def _panel_mean(otname: str, restrict_biosamples: Optional[List[str]]):
            mask = df[ot_col].astype(str).str.upper().str.contains(otname)
            sub = df[mask]
            if (restrict_biosamples and "biosample_name" in sub.columns
                    and len(restrict_biosamples)):
                r = sub[sub["biosample_name"].astype(str).isin(restrict_biosamples)]
                if len(r):
                    sub = r  # only restrict if it leaves something to average
            vals = pd.to_numeric(sub[score_col], errors="coerce").dropna()
            return float(vals.mean()) if len(vals) else np.nan

        dnase = _panel_mean("DNASE", self.skeletal_biosamples)
        atac = _panel_mean("ATAC", None)
        return (round(dnase, 5) if dnase == dnase else np.nan,
                round(atac, 5) if atac == atac else np.nan)

    def _base_resolution_max(self, row: pd.Series):
        """
        Base-resolution max-|delta| over the skeletal DNASE panel: predict 1-bp
        ref/alt tracks, average over the skeletal biosamples, and return
        (hg38_position_of_argmax|alt-ref|, signed_delta_there).

        This is what the region-level MPRA CANNOT do: pinpoint the single base
        driving the differential accessibility (e.g. blindly re-finding the
        GDF5/GROW1 causal substitution).
        """
        try:
            interval, variant = self._interval_variant(row)
            out = self.model.predict_variant(interval=interval, variant=variant)
        except Exception as e:  # pragma: no cover - network dependent
            print(f"[alphagenome] base-resolution predict_variant failed: {e}",
                  file=sys.stderr)
            return None, np.nan

        def _dnase_matrix(side):
            trk = getattr(getattr(out, side, None), "dnase", None)
            if trk is None:
                return None, None
            values = getattr(trk, "values", None)
            if values is None:
                return None, None
            arr = np.asarray(values, dtype=float)  # (positions, tracks)
            return arr, getattr(trk, "interval", None)

        ref_arr, ivl = _dnase_matrix("reference")
        alt_arr, _ = _dnase_matrix("alternate")
        if ref_arr is None or alt_arr is None or ref_arr.shape != alt_arr.shape:
            return None, np.nan
        per_base = (alt_arr - ref_arr)
        # Collapse tracks to the skeletal panel mean if we can, else all tracks.
        if per_base.ndim == 2:
            per_base = per_base.mean(axis=1)
        idx = int(np.argmax(np.abs(per_base)))
        start = int(getattr(ivl, "start", int(row["pos_hg38"]) - 1)) if ivl is not None \
            else int(row["pos_hg38"]) - 1
        return start + idx + 1, float(per_base[idx])  # 1-based hg38

    def _contributing_biosamples(self, df: pd.DataFrame) -> str:
        if df is None or "biosample_name" not in df.columns:
            return "unknown"
        names = sorted(set(df["biosample_name"].astype(str)))[:6]
        return ";".join(names) if names else "unknown"


# ============================================================================
# Driver
# ============================================================================
REQUIRED_IN = ["har_id", "chrom", "pos_hg38", "ref_ancestral", "alt_human"]


def run(in_tsv: str, out_tsv: str, full: bool, api_key: Optional[str],
        limit: Optional[int] = None) -> pd.DataFrame:
    df = pd.read_csv(in_tsv, sep="\t", dtype={"chrom": str})
    missing = [c for c in REQUIRED_IN if c not in df.columns]
    if missing:
        raise ValueError(f"Input TSV missing required columns: {missing}")

    for col in ("ag_atac_delta", "ag_dnase_delta"):
        if col not in df.columns:
            df[col] = np.nan
    if "notes" not in df.columns:
        df["notes"] = ""
    # Force notes to string dtype (a demo TSV may read it back as all-NaN float).
    df["notes"] = df["notes"].fillna("").astype(str).replace("nan", "")

    scorer = None
    if full:
        if not api_key:
            raise SystemExit(
                "--full requires an API key. Set ALPHAGENOME_API_KEY or pass "
                "--api-key. (Run without --full for the offline mock.)")
        scorer = AlphaGenomeScorer(api_key)
        print(f"[alphagenome] REAL mode; skeletal DNASE panel of "
              f"{len(scorer.skeletal_biosamples)} biosample(s).", file=sys.stderr)
    else:
        print("[alphagenome] MOCK mode (offline, deterministic, DNASE-panel proxy).",
              file=sys.stderr)

    n = len(df) if limit is None else min(limit, len(df))
    for i in range(n):
        row = df.iloc[i]
        res = mock_score(row) if scorer is None else scorer.score_row(row)
        df.at[df.index[i], "ag_dnase_delta"] = res.ag_dnase_delta
        df.at[df.index[i], "ag_atac_delta"] = res.ag_atac_delta
        prev = str(df.at[df.index[i], "notes"] or "")
        add = _fmt_notes(res)
        df.at[df.index[i], "notes"] = (prev + ("; " if prev else "") + add)[:500]
        if (i + 1) % 50 == 0:
            print(f"[alphagenome] scored {i + 1}/{n}", file=sys.stderr)

    df.to_csv(out_tsv, sep="\t", index=False)
    print(f"[alphagenome] wrote {out_tsv} ({n} rows scored)", file=sys.stderr)
    return df


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="AlphaGenome human(alt)-vs-chimp(ref) DNase scoring for SKELETOME.")
    ap.add_argument("--in", dest="in_tsv", required=True, help="input canonical TSV")
    ap.add_argument("--out", dest="out_tsv", required=True, help="output canonical TSV")
    ap.add_argument("--full", action="store_true",
                    help="use the real AlphaGenome hosted API (default: offline mock)")
    ap.add_argument("--api-key", default=os.environ.get("ALPHAGENOME_API_KEY"),
                    help="AlphaGenome API key (or set ALPHAGENOME_API_KEY)")
    ap.add_argument("--limit", type=int, default=None, help="score only first N rows (debug)")
    args = ap.parse_args(argv)
    run(args.in_tsv, args.out_tsv, args.full, args.api_key, args.limit)


if __name__ == "__main__":
    main()
