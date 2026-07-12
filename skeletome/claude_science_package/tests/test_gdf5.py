"""Self-red-team gate: the GDF5 / HACNS1 controls MUST survive the pipeline.

Project decision #6: Claude self-red-teams the pipeline to catch any silent
filter that would drop its own positive control. This test suite is that gate.
It runs the full mock pipeline (substitutions -> constraint -> gBGC) with NO
downloads and asserts:

1. Every control substitution is enumerated and correctly labeled.
2. Controls parse into a schema-valid table.
3. Controls survive the constraint annotation and can be made ``constrained``.
4. Controls are NOT spuriously ``gbgc_flag``-ged out of the candidate pool.
5. The candidate rule (constrained AND NOT gbgc_flag AND skeletal effect) would
   retain a GDF5 control given a skeletal effect -- i.e. no silent filter drops it.

Run with: pytest tests/test_gdf5.py  (from the package root, with code/ on sys.path)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Make code/ importable whether pytest is run from the repo root or tests/.
_CODE_DIR = Path(__file__).resolve().parents[1] / "code"
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import constraint  # noqa: E402
import gbgc  # noqa: E402
import schema  # noqa: E402
import substitutions  # noqa: E402
from constraint import MockPhyloPScorer, annotate_constraint  # noqa: E402
from gbgc import MockRecombinationMap, annotate_gbgc  # noqa: E402
from schema import CONTROL_LABELS, validate  # noqa: E402
from substitutions import (  # noqa: E402
    CONTROL_SUBSTITUTIONS,
    build_substitution_table,
    control_rows,
)

CONTROL_HAR_IDS = {"GDF5-GROW1", "GDF5-R4", "HACNS1"}


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture()
def base_table() -> pd.DataFrame:
    """Full mock substitution table (background + spiked controls)."""
    df, stats = build_substitution_table(mock=True, include_controls=True)
    assert stats["n_controls"] == len(CONTROL_SUBSTITUTIONS)
    return df


@pytest.fixture()
def constraint_overrides():
    """Force all three controls to be strongly constrained (phyloP > 2.27)."""
    return {
        (c.chrom.replace("chr", ""), c.pos_hg38): 5.0 for c in CONTROL_SUBSTITUTIONS
    }


# --------------------------------------------------------------------------- #
# 1. Enumeration + labeling
# --------------------------------------------------------------------------- #
def test_controls_are_enumerated_and_labeled(base_table: pd.DataFrame) -> None:
    present = set(base_table.loc[base_table["is_control"] != "none", "har_id"])
    assert CONTROL_HAR_IDS <= present, f"missing controls: {CONTROL_HAR_IDS - present}"

    for har_id in CONTROL_HAR_IDS:
        row = base_table.loc[base_table["har_id"] == har_id]
        assert len(row) == 1, f"expected exactly one row for {har_id}"
        label = row["is_control"].iloc[0]
        assert label in CONTROL_LABELS and label != "none"


def test_control_rows_helper_matches_spec() -> None:
    rows = control_rows()
    assert {r.har_id for r in rows} == CONTROL_HAR_IDS
    for r in rows:
        assert r.ref_ancestral in set("ACGT")
        assert r.alt_human in set("ACGT")
        assert r.ref_ancestral != r.alt_human
        assert r.chrom.startswith("chr")
        assert r.pos_hg38 > 0


def test_gdf5_control_coordinates_are_the_locked_values() -> None:
    """Guard the project-locked hg38 coordinates so a refactor cannot drift them."""
    by_id = {c.har_id: c for c in CONTROL_SUBSTITUTIONS}
    assert by_id["GDF5-GROW1"].chrom == "chr20"
    assert by_id["GDF5-GROW1"].pos_hg38 == 35_364_817  # rs4911178
    assert by_id["GDF5-R4"].chrom == "chr20"
    assert by_id["GDF5-R4"].pos_hg38 == 35_319_358  # rs6060369
    assert by_id["HACNS1"].chrom == "chr2"


# --------------------------------------------------------------------------- #
# 2. Schema validity
# --------------------------------------------------------------------------- #
def test_table_is_schema_valid(base_table: pd.DataFrame) -> None:
    validate(base_table)
    assert list(base_table.columns) == schema.COLUMNS


# --------------------------------------------------------------------------- #
# 3. Controls survive constraint annotation
# --------------------------------------------------------------------------- #
def test_controls_survive_constraint(base_table, constraint_overrides) -> None:
    scorer = MockPhyloPScorer(overrides=constraint_overrides)
    annotated = annotate_constraint(base_table, scorer=scorer, rocc_set=constraint.RoCCSet.empty())

    # No rows dropped.
    assert len(annotated) == len(base_table)

    for har_id in CONTROL_HAR_IDS:
        row = annotated.loc[annotated["har_id"] == har_id]
        assert len(row) == 1
        assert bool(row["constrained"].iloc[0]) is True, f"{har_id} not constrained"
        assert row["phylop_241"].iloc[0] > schema.PHYLOP_CONSTRAINED_THRESHOLD


def test_constraint_threshold_boundary() -> None:
    """A phyloP exactly at 2.27 is NOT constrained (strict > threshold)."""
    df = substitutions.rows_to_frame(control_rows())
    at_threshold = {
        (c.chrom.replace("chr", ""), c.pos_hg38): schema.PHYLOP_CONSTRAINED_THRESHOLD
        for c in CONTROL_SUBSTITUTIONS
    }
    annotated = annotate_constraint(
        df, scorer=MockPhyloPScorer(overrides=at_threshold), rocc_set=constraint.RoCCSet.empty()
    )
    assert not annotated["constrained"].any()


# --------------------------------------------------------------------------- #
# 4. Controls are not spuriously gBGC-flagged
# --------------------------------------------------------------------------- #
def test_controls_not_spuriously_gbgc_flagged(base_table) -> None:
    # Low recombination everywhere -> no WtoS control should be flagged.
    low_recomb = MockRecombinationMap(
        overrides={
            (c.chrom.replace("chr", ""), c.pos_hg38): 0.5 for c in CONTROL_SUBSTITUTIONS
        }
    )
    annotated = annotate_gbgc(base_table, recomb_map=low_recomb, hotspots=gbgc.HotspotSet.empty())

    for har_id in CONTROL_HAR_IDS:
        row = annotated.loc[annotated["har_id"] == har_id]
        assert len(row) == 1
        assert bool(row["gbgc_flag"].iloc[0]) is False, f"{har_id} wrongly gbgc-flagged"


def test_gbgc_classification_is_correct_for_controls() -> None:
    """Sanity-check the W/S polarity for each control's locked alleles."""
    from gbgc import classify_gbgc

    by_id = {c.har_id: c for c in CONTROL_SUBSTITUTIONS}
    for har_id, spec in by_id.items():
        cls = classify_gbgc(spec.ref_ancestral, spec.alt_human)
        assert cls in ("WtoS", "StoW", "neutral")
        # cross-check against manual W/S membership
        a_strong = spec.ref_ancestral in "GC"
        d_strong = spec.alt_human in "GC"
        expected = (
            "WtoS" if (not a_strong and d_strong)
            else "StoW" if (a_strong and not d_strong)
            else "neutral"
        )
        assert cls == expected


def test_wtos_control_in_hotspot_is_flagged_only_when_expected() -> None:
    """A WtoS control DOES get flagged in a hotspot -- flag logic is not dead."""
    from gbgc import classify_gbgc

    # Build a one-row synthetic WtoS control to exercise the positive branch.
    row = schema.SubstitutionRow(
        har_id="synthetic-WtoS",
        chrom="chr3",
        pos_hg38=1_000_000,
        ref_ancestral="A",
        alt_human="G",
        is_control="none",
    )
    assert classify_gbgc("A", "G") == "WtoS"
    df = schema.rows_to_frame([row])

    hot = MockRecombinationMap(overrides={("3", 1_000_000): 25.0})  # elevated
    annotated = annotate_gbgc(df, recomb_map=hot, hotspots=gbgc.HotspotSet.empty())
    assert bool(annotated["gbgc_flag"].iloc[0]) is True


# --------------------------------------------------------------------------- #
# 5. End-to-end: candidate rule retains a GDF5 control given a skeletal effect
# --------------------------------------------------------------------------- #
def test_full_pipeline_retains_gdf5_control(base_table, constraint_overrides) -> None:
    """Silent-filter red-team: constrained + not-gbgc + skeletal effect keeps GDF5."""
    # constraint (force controls constrained)
    df = annotate_constraint(
        base_table,
        scorer=MockPhyloPScorer(overrides=constraint_overrides),
        rocc_set=constraint.RoCCSet.empty(),
    )
    # gBGC (low recomb at controls -> not flagged)
    low_recomb = MockRecombinationMap(
        overrides={
            (c.chrom.replace("chr", ""), c.pos_hg38): 0.5 for c in CONTROL_SUBSTITUTIONS
        }
    )
    df = annotate_gbgc(df, recomb_map=low_recomb, hotspots=gbgc.HotspotSet.empty())

    # Simulate a downstream skeletal effect on the GDF5 controls (AlphaGenome
    # phase would set this; we inject a non-trivial delta so the candidate rule
    # can be exercised here without the AG dependency).
    gdf5_mask = df["har_id"].isin(["GDF5-GROW1", "GDF5-R4"])
    df.loc[gdf5_mask, "ag_atac_delta"] = -0.3  # derived reduces activity (expected)

    # Candidate rule per schema: constrained AND NOT gbgc_flag AND skeletal effect.
    skeletal_effect = df["ag_atac_delta"].abs() > 0.1
    candidate = df["constrained"] & (~df["gbgc_flag"]) & skeletal_effect

    for har_id in ("GDF5-GROW1", "GDF5-R4"):
        idx = df.index[df["har_id"] == har_id][0]
        assert candidate.loc[idx], (
            f"{har_id} was silently filtered out of the candidate pool -- "
            "a filter is dropping the positive control"
        )


def test_no_rows_lost_across_phases(base_table, constraint_overrides) -> None:
    n0 = len(base_table)
    df = annotate_constraint(
        base_table,
        scorer=MockPhyloPScorer(overrides=constraint_overrides),
        rocc_set=constraint.RoCCSet.empty(),
    )
    assert len(df) == n0
    df = annotate_gbgc(df, recomb_map=MockRecombinationMap(), hotspots=gbgc.HotspotSet.empty())
    assert len(df) == n0
    validate(df)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
