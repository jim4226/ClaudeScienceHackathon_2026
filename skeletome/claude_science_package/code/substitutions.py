"""Enumerate human-specific substitutions per HAR and spike in labeled controls.

Pipeline phase P1. This module turns the Whalen & Pollard 2023 human-chimp
fixed-difference tables (hg19; GEO GSE110760 / PMC10023452) plus the zooHARs
region set (Keough 2023, n=312, hg38; Science doi:10.1126/science.abm1696
Table S1) into a canonical table of one row per human-specific substitution, in
hg38 coordinates.

Design decisions
----------------
* The Whalen/Pollard tables are hg19. We liftOver every substitution to hg38.
  liftOver is invoked as an external subprocess (UCSC ``liftOver`` binary +
  ``hg19ToHg38.over.chain.gz``); this module wraps it but never invents a mapping.
  Positions that fail to lift are dropped and counted (never silently coerced).
* Ancestral vs derived: the "ancestral" allele is the inferred non-human primate
  allele (the chimp/ancestor base from the fixed-difference table); the "derived"
  allele is the human base. ``ref_ancestral`` = ancestral, ``alt_human`` = derived.
  NOTE this is deliberately NOT the hg38 reference-vs-alt convention -- for a
  human-specific fixed difference the hg38 reference base normally *equals* the
  human/derived allele. Downstream AlphaGenome scoring is run ancestral -> derived
  so a positive delta means "the human change increased accessibility".
* Self-red-team gate (project decision #6): GDF5-GROW1, GDF5-R4 and HACNS1 are
  spiked in as explicitly labeled control rows via :func:`control_rows` so no
  silent filter downstream can drop the positive controls without a test failing.

Mock-data path
--------------
Every function accepts explicit inputs; :func:`build_substitution_table` with
``mock=True`` runs the whole phase with a tiny built-in fixture and NO downloads
and NO liftOver binary, so the package is runnable out of the box.

Verified locators (confirm live before a real run)
--------------------------------------------------
* Whalen & Pollard fixed differences: GEO GSE110760
* zooHARs Table S1: Science doi:10.1126/science.abm1696
* liftOver chain: https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz
* liftOver binary: https://hgdownload.soe.ucsc.edu/admin/exe/
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from schema import SubstitutionRow, coerce, rows_to_frame

__all__ = [
    "Substitution",
    "LiftoverResult",
    "CONTROL_SUBSTITUTIONS",
    "control_rows",
    "read_whalen_pollard_table",
    "liftover_hg19_to_hg38",
    "build_substitution_table",
    "MOCK_WHALEN_POLLARD_ROWS",
]

_BASES = frozenset("ACGT")


@dataclass(frozen=True)
class Substitution:
    """A single human-specific fixed difference before/after liftOver.

    ``pos`` is 1-based (VCF/UCSC-browser style). ``ancestral`` is the inferred
    non-human allele; ``derived`` is the human allele.
    """

    har_id: str
    chrom: str
    pos: int
    ancestral: str
    derived: str
    target_gene_hypothesis: str = ""

    def __post_init__(self) -> None:
        for allele, name in ((self.ancestral, "ancestral"), (self.derived, "derived")):
            if allele.upper() not in _BASES:
                raise ValueError(
                    f"{name} allele {allele!r} for {self.har_id} is not a single "
                    "base in {A,C,G,T}"
                )
        if self.ancestral.upper() == self.derived.upper():
            raise ValueError(
                f"ancestral == derived ({self.ancestral}) for {self.har_id}:{self.pos} "
                "-- not a substitution"
            )


@dataclass(frozen=True)
class LiftoverResult:
    """Outcome of lifting a set of substitutions between assemblies."""

    lifted: List[Substitution]
    dropped: List[Substitution]

    @property
    def n_lifted(self) -> int:
        return len(self.lifted)

    @property
    def n_dropped(self) -> int:
        return len(self.dropped)


# --------------------------------------------------------------------------- #
# CONTROL SET (hg38). Frozen coordinates -- see project context "GDF5 controls".
#
# These are spiked into every run as labeled rows. The alleles below use the
# ancestral->derived convention. Where a precise ancestral base is not yet
# hand-verified from primary literature it is marked with a TODO and given the
# most-cited value; the *coordinate* and *is_control label* are the load-bearing
# parts for the self-red-team gate (the test asserts these rows survive filters),
# so an unverified allele letter does not weaken the gate.
#
# Sources to confirm alleles against before publication:
#   rs4911178 (GROW1/hip)  chr20:35,364,817  -- Capellini 2017; dbSNP
#   rs6060369 (R4/knee)    chr20:35,319,358  -- Capellini 2017; dbSNP
#   HACNS1 (near GBX2)     chr2 (hg38)       -- lift from hg19; Prabhakar 2008
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ControlSpec:
    """A frozen control substitution + its provenance label."""

    is_control: str            # schema CONTROL_LABELS value
    har_id: str
    chrom: str
    pos_hg38: int
    ref_ancestral: str
    alt_human: str
    target_gene_hypothesis: str
    notes: str


CONTROL_SUBSTITUTIONS: Tuple[ControlSpec, ...] = (
    ControlSpec(
        is_control="GDF5-GROW1",
        har_id="GDF5-GROW1",
        chrom="chr20",
        pos_hg38=35_364_817,          # rs4911178, hg38 (project-locked)
        ref_ancestral="G",            # TODO verify ancestral allele vs dbSNP rs4911178
        alt_human="A",                # TODO verify derived allele vs dbSNP rs4911178
        target_gene_hypothesis="GDF5",
        notes=(
            "Positive control: GROW1 hip enhancer (Capellini 2017). Derived allele "
            "expected to REDUCE enhancer activity (~0.72x). rs4911178. "
            "TODO confirm alleles against dbSNP before publication."
        ),
    ),
    ControlSpec(
        is_control="GDF5-R4",
        har_id="GDF5-R4",
        chrom="chr20",
        pos_hg38=35_319_358,          # rs6060369, hg38 (project-locked)
        ref_ancestral="C",            # TODO verify ancestral allele vs dbSNP rs6060369
        alt_human="T",                # TODO verify derived allele vs dbSNP rs6060369
        target_gene_hypothesis="GDF5",
        notes=(
            "Positive control: R4 knee enhancer (Capellini 2017). rs6060369. "
            "TODO confirm alleles against dbSNP before publication."
        ),
    ),
    ControlSpec(
        is_control="HACNS1",
        har_id="HACNS1",
        # HACNS1 / HAR2 / 2xHAR.3 near GBX2, chr2q37.3. hg19 ~chr2:236,773,979.
        # TODO: replace with the exact hg38 substitution coordinate lifted from
        # the zooHARs Table S1 / Prabhakar 2008 record. The value below is a
        # documented placeholder in the correct locus so the control row exists;
        # constraint/gBGC queries will still run against it. Verify via:
        #   liftOver hg19:chr2:236,773,979 -> hg38  (expected ~chr2:235,865,331)
        chrom="chr2",
        pos_hg38=235_865_331,         # TODO verify exact hg38 substitution position
        ref_ancestral="A",            # TODO verify ancestral allele (chimp) Prabhakar 2008
        alt_human="G",                # TODO verify human-specific derived allele
        target_gene_hypothesis="GBX2",
        notes=(
            "Positive control: HACNS1/HAR2 limb enhancer, gain-of-function near "
            "GBX2 (Prabhakar 2008). Coordinate + allele are documented placeholders "
            "in the correct locus -- TODO lift exact substitution from zooHARs S1."
        ),
    ),
)


def control_rows() -> List[SubstitutionRow]:
    """Return the labeled control substitutions as :class:`SubstitutionRow`.

    These are appended to every table so that downstream filters (constraint,
    gBGC, candidate selection) can be red-teamed: a test asserts they survive.
    """
    rows: List[SubstitutionRow] = []
    for c in CONTROL_SUBSTITUTIONS:
        rows.append(
            SubstitutionRow(
                har_id=c.har_id,
                chrom=c.chrom,
                pos_hg38=c.pos_hg38,
                ref_ancestral=c.ref_ancestral,
                alt_human=c.alt_human,
                target_gene_hypothesis=c.target_gene_hypothesis,
                is_control=c.is_control,
                notes=c.notes,
            )
        )
    return rows


# --------------------------------------------------------------------------- #
# Whalen/Pollard table reader
# --------------------------------------------------------------------------- #
# Column names are configurable because the exact header of GSE110760 supplements
# should be confirmed against the deposited file. Defaults follow the documented
# schema; override via ``columns=`` if the download differs.
_DEFAULT_WP_COLUMNS = {
    "har_id": "har_id",
    "chrom": "chrom",
    "pos": "pos",              # 1-based hg19 position
    "ancestral": "ancestral",  # inferred chimp/ancestor allele
    "derived": "derived",      # human allele
    "target_gene_hypothesis": "target_gene",
}


def read_whalen_pollard_table(
    path: str | Path,
    *,
    columns: Optional[Dict[str, str]] = None,
    sep: str = "\t",
) -> List[Substitution]:
    """Parse a Whalen/Pollard human-chimp fixed-difference table (hg19).

    Parameters
    ----------
    path:
        Path to the TSV/CSV of fixed differences.
    columns:
        Mapping from logical field -> actual column header in the file. Keys:
        ``har_id, chrom, pos, ancestral, derived, target_gene_hypothesis``.
        ``target_gene_hypothesis`` is optional and defaults to empty.
    sep:
        Field delimiter (``"\\t"`` by default).

    Returns
    -------
    List of :class:`Substitution` in hg19 coordinates.

    Notes
    -----
    TODO confirm the exact header/columns of the GSE110760 supplement before a
    real run. If the deposited table encodes the substitution as ``ref``/``alt``
    against hg19 rather than ancestral/derived, map accordingly: for a
    human-specific fixed difference the hg19 reference base is the human/derived
    allele, so ``ancestral`` is the non-reference (chimp) base.
    """
    cols = {**_DEFAULT_WP_COLUMNS, **(columns or {})}
    subs: List[Substitution] = []
    with open(path, "r", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=sep)
        _require_columns(reader.fieldnames, cols)
        for rec in reader:
            gene = (
                rec.get(cols["target_gene_hypothesis"], "")
                if cols["target_gene_hypothesis"] in (reader.fieldnames or [])
                else ""
            )
            subs.append(
                Substitution(
                    har_id=rec[cols["har_id"]].strip(),
                    chrom=_normalize_chrom(rec[cols["chrom"]]),
                    pos=int(rec[cols["pos"]]),
                    ancestral=rec[cols["ancestral"]].strip().upper(),
                    derived=rec[cols["derived"]].strip().upper(),
                    target_gene_hypothesis=(gene or "").strip(),
                )
            )
    return subs


def _require_columns(fieldnames: Optional[Iterable[str]], cols: Dict[str, str]) -> None:
    present = set(fieldnames or [])
    required = {cols[k] for k in ("har_id", "chrom", "pos", "ancestral", "derived")}
    missing = required - present
    if missing:
        raise ValueError(
            f"Whalen/Pollard table missing required columns {sorted(missing)}. "
            f"Present: {sorted(present)}. Pass columns=... to remap."
        )


def _normalize_chrom(chrom: str) -> str:
    chrom = chrom.strip()
    return chrom if chrom.startswith("chr") else f"chr{chrom}"


# --------------------------------------------------------------------------- #
# liftOver hg19 -> hg38
# --------------------------------------------------------------------------- #
def liftover_hg19_to_hg38(
    subs: List[Substitution],
    chain_path: str | Path,
    *,
    liftover_bin: str = "liftOver",
    min_match: float = 0.95,
) -> LiftoverResult:
    """Lift substitutions from hg19 to hg38 using the UCSC ``liftOver`` binary.

    Each substitution is written as a 1-bp BED interval (0-based half-open:
    ``pos-1``..``pos``) whose name encodes the row index so we can rejoin
    alleles after lifting. Positions that fail to map are returned in ``dropped``
    -- they are never silently coerced.

    Parameters
    ----------
    subs:
        hg19 substitutions from :func:`read_whalen_pollard_table`.
    chain_path:
        Path to ``hg19ToHg38.over.chain.gz``.
    liftover_bin:
        Name/path of the UCSC liftOver executable (must be on PATH or absolute).
    min_match:
        ``-minMatch`` passed to liftOver.

    Returns
    -------
    :class:`LiftoverResult` with lifted (hg38) and dropped substitutions.

    Raises
    ------
    FileNotFoundError
        If the liftOver binary or chain file is not available.
    RuntimeError
        If liftOver exits non-zero.
    """
    if shutil.which(liftover_bin) is None and not Path(liftover_bin).exists():
        raise FileNotFoundError(
            f"liftOver binary {liftover_bin!r} not found. Install from "
            "https://hgdownload.soe.ucsc.edu/admin/exe/ or use mock=True."
        )
    chain_path = Path(chain_path)
    if not chain_path.exists():
        raise FileNotFoundError(f"liftOver chain not found: {chain_path}")

    index: Dict[str, Substitution] = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        in_bed = tmp_dir / "in.bed"
        out_bed = tmp_dir / "out.bed"
        unmapped = tmp_dir / "unmapped.bed"

        with open(in_bed, "w", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t")
            for i, s in enumerate(subs):
                key = str(i)
                index[key] = s
                # BED is 0-based half-open; a 1-based pos -> [pos-1, pos)
                writer.writerow([s.chrom, s.pos - 1, s.pos, key])

        cmd = [
            liftover_bin,
            f"-minMatch={min_match}",
            str(in_bed),
            str(chain_path),
            str(out_bed),
            str(unmapped),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"liftOver failed (exit {proc.returncode}): {proc.stderr.strip()}"
            )

        lifted: List[Substitution] = []
        lifted_keys: set = set()
        with open(out_bed, "r", newline="") as fh:
            for row in csv.reader(fh, delimiter="\t"):
                if not row or row[0].startswith("#"):
                    continue
                chrom, start, _end, key = row[0], int(row[1]), int(row[2]), row[3]
                src = index[key]
                lifted.append(
                    Substitution(
                        har_id=src.har_id,
                        chrom=_normalize_chrom(chrom),
                        pos=start + 1,  # back to 1-based
                        ancestral=src.ancestral,
                        derived=src.derived,
                        target_gene_hypothesis=src.target_gene_hypothesis,
                    )
                )
                lifted_keys.add(key)

    dropped = [index[k] for k in index if k not in lifted_keys]
    return LiftoverResult(lifted=lifted, dropped=dropped)


# --------------------------------------------------------------------------- #
# Mock fixture (no downloads, no liftOver binary)
# --------------------------------------------------------------------------- #
# A tiny set of plausible hg38 substitutions used when ``mock=True``. Coordinates
# are illustrative; the GDF5/HACNS1 rows come from control_rows(), not here.
MOCK_WHALEN_POLLARD_ROWS: Tuple[Substitution, ...] = (
    Substitution("zooHAR_0001", "chr1", 1_000_100, "A", "G", "WNT4"),
    Substitution("zooHAR_0001", "chr1", 1_000_180, "C", "T", "WNT4"),
    Substitution("zooHAR_0042", "chr7", 20_500_000, "G", "C", "SHH"),
    Substitution("zooHAR_0113", "chr20", 35_400_000, "T", "A", "GDF5"),
    Substitution("zooHAR_0200", "chr12", 48_000_050, "A", "T", "SP7"),
)


def build_substitution_table(
    *,
    wp_table: Optional[str | Path] = None,
    chain_path: Optional[str | Path] = None,
    wp_columns: Optional[Dict[str, str]] = None,
    liftover_bin: str = "liftOver",
    include_controls: bool = True,
    mock: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """End-to-end phase P1: produce the canonical substitution table (hg38).

    Parameters
    ----------
    wp_table:
        Path to the Whalen/Pollard hg19 fixed-difference table. Required unless
        ``mock=True``.
    chain_path:
        Path to ``hg19ToHg38.over.chain.gz``. Required unless ``mock=True``.
    wp_columns:
        Optional column remap for :func:`read_whalen_pollard_table`.
    liftover_bin:
        liftOver executable name/path.
    include_controls:
        If ``True`` (default) append the labeled GDF5/HACNS1 control rows. Keep
        this ``True`` for real runs -- it is the self-red-team gate.
    mock:
        If ``True``, skip all I/O: use :data:`MOCK_WHALEN_POLLARD_ROWS` already in
        hg38 and do not call liftOver. Lets the package run with no downloads.

    Returns
    -------
    (df, stats) where ``df`` is a schema-valid DataFrame (one row per
    substitution) and ``stats`` reports counts:
    ``{"n_input", "n_lifted", "n_dropped", "n_controls", "n_total"}``.
    """
    if mock:
        hg38_subs = list(MOCK_WHALEN_POLLARD_ROWS)
        stats = {
            "n_input": len(hg38_subs),
            "n_lifted": len(hg38_subs),
            "n_dropped": 0,
        }
    else:
        if wp_table is None or chain_path is None:
            raise ValueError(
                "wp_table and chain_path are required unless mock=True"
            )
        hg19_subs = read_whalen_pollard_table(wp_table, columns=wp_columns)
        result = liftover_hg19_to_hg38(
            hg19_subs, chain_path, liftover_bin=liftover_bin
        )
        hg38_subs = result.lifted
        stats = {
            "n_input": len(hg19_subs),
            "n_lifted": result.n_lifted,
            "n_dropped": result.n_dropped,
        }

    rows: List[SubstitutionRow] = [
        SubstitutionRow(
            har_id=s.har_id,
            chrom=s.chrom,
            pos_hg38=s.pos,
            ref_ancestral=s.ancestral,
            alt_human=s.derived,
            target_gene_hypothesis=s.target_gene_hypothesis,
            is_control="none",
        )
        for s in hg38_subs
    ]

    if include_controls:
        controls = control_rows()
        rows.extend(controls)
        stats["n_controls"] = len(controls)
    else:
        stats["n_controls"] = 0

    df = rows_to_frame(rows)
    df = coerce(df)
    stats["n_total"] = len(df)
    return df, stats
