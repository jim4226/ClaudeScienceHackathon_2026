"""Deep mammalian constraint annotation (Zoonomia 241-way phyloP + RoCCs).

Pipeline phase P2 (constraint half). For every substitution position we query the
Zoonomia 241-way phyloP score (hg38) and flag:

* ``phylop_241``   -- the per-base phyloP score at the substitution position.
* ``constrained``  -- ``phylop_241 > 2.27`` (project-locked threshold).
* ``rocc``         -- whether the position falls inside a Zoonomia RoCC
                      (Region of Constrained Conservation) interval.

Crucial efficiency + correctness note
-------------------------------------
The 241-way phyloP bigWig is ~9 GB. We NEVER stream the whole file: we open it
once with pyBigWig and query ONLY the single-base positions we care about via
``bw.values(chrom, start, start+1)``. bigWig uses 0-based half-open coordinates,
so a 1-based ``pos_hg38`` maps to the half-open interval ``[pos-1, pos)``.

Missing-data handling: pyBigWig returns ``nan`` for bases with no score. We keep
the ``nan`` (never coerce to 0) and treat ``constrained`` as ``False`` there --
absence of a conservation score is not evidence of constraint.

Mock-data path
--------------
Pass ``bigwig_path=None`` (or ``mock=True`` to :func:`annotate_constraint`) to use
a deterministic in-memory scorer and an empty RoCC set, so this phase runs with no
9 GB download and without pyBigWig installed.

Verified locators
-----------------
* phyloP bigWig: https://hgdownload.soe.ucsc.edu/goldenPath/hg38/cactus241way/hg38.cactus241way.phyloP.bw
* RoCCs mask:    https://cgl.gi.ucsc.edu/data/cactus/zoonomia-2021-track-hub/hg38/RoCCs.bed.gz
* pyBigWig API:  bw = pyBigWig.open(path); bw.values(chrom, start, end) -> list[float]
                 (0-based half-open; missing bases -> nan). Verified against
                 https://github.com/deeptools/pyBigWig
"""

from __future__ import annotations

import gzip
from bisect import bisect_right
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple

import numpy as np
import pandas as pd

from schema import PHYLOP_CONSTRAINED_THRESHOLD, coerce, validate

__all__ = [
    "PhyloPScorer",
    "BigWigPhyloPScorer",
    "MockPhyloPScorer",
    "RoCCSet",
    "load_roccs",
    "annotate_constraint",
]


class PhyloPScorer(Protocol):
    """Anything that can return a phyloP score for a single (chrom, pos) base."""

    def score(self, chrom: str, pos_hg38: int) -> float:
        """Return the phyloP score at 1-based ``pos_hg38`` (nan if unavailable)."""
        ...


class BigWigPhyloPScorer:
    """Query the 241-way phyloP bigWig one base at a time via pyBigWig.

    Opens the file once and reuses the handle. Import of ``pyBigWig`` is lazy so
    the rest of the pipeline can run in the mock path without the dependency.
    """

    def __init__(self, bigwig_path: str | Path) -> None:
        try:
            import pyBigWig  # noqa: WPS433 (lazy import by design)
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "pyBigWig is required for BigWigPhyloPScorer. "
                "Install with `pip install pyBigWig`, or use MockPhyloPScorer."
            ) from exc

        path = Path(bigwig_path)
        if not path.exists():
            raise FileNotFoundError(f"phyloP bigWig not found: {path}")

        self._bw = pyBigWig.open(str(path))
        if self._bw is None:  # pyBigWig.open returns None on failure
            raise IOError(f"pyBigWig failed to open {path}")
        self._chroms: Dict[str, int] = dict(self._bw.chroms() or {})

    def score(self, chrom: str, pos_hg38: int) -> float:
        """Return phyloP at 1-based ``pos_hg38`` using a 0-based half-open query."""
        chrom = _match_chrom(chrom, self._chroms)
        if chrom is None:
            return float("nan")
        start = pos_hg38 - 1  # 1-based -> 0-based
        end = pos_hg38        # half-open
        if start < 0 or end > self._chroms[chrom]:
            return float("nan")
        try:
            vals = self._bw.values(chrom, start, end)
        except (RuntimeError, ValueError):
            return float("nan")
        if not vals:
            return float("nan")
        v = vals[0]
        return float(v) if v is not None else float("nan")

    def close(self) -> None:
        if getattr(self, "_bw", None) is not None:
            self._bw.close()
            self._bw = None

    def __enter__(self) -> "BigWigPhyloPScorer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class MockPhyloPScorer:
    """Deterministic phyloP scorer for the no-download path and tests.

    Scores are a stable pseudo-random function of (chrom, pos) in a plausible
    phyloP range, plus an optional ``overrides`` map so tests can pin the score
    at specific control positions (e.g. force a GDF5 control to be constrained).
    """

    def __init__(
        self,
        *,
        overrides: Optional[Dict[Tuple[str, int], float]] = None,
        default_constrained: bool = True,
    ) -> None:
        self._overrides = dict(overrides or {})
        self._default_constrained = default_constrained

    def score(self, chrom: str, pos_hg38: int) -> float:
        key = (_strip_chr(chrom), pos_hg38)
        if key in self._overrides:
            return self._overrides[key]
        # Deterministic value seeded by position. Bias above/below the 2.27
        # threshold according to default_constrained so mock runs are meaningful.
        seed = (hash(key) & 0xFFFF) / 0xFFFF  # in [0, 1)
        if self._default_constrained:
            return float(2.27 + 0.01 + seed * 5.0)   # ~[2.28, 7.28)
        return float(-1.0 + seed * 3.0)              # ~[-1.0, 2.0)


# --------------------------------------------------------------------------- #
# RoCC (Region of Constrained Conservation) overlap
# --------------------------------------------------------------------------- #
class RoCCSet:
    """Fast point-in-interval lookup over RoCC BED intervals (0-based half-open).

    Intervals per chromosome are stored sorted by start; membership uses binary
    search over starts plus a running max-end to be robust to overlapping/
    unsorted-by-end intervals.
    """

    def __init__(self, intervals_by_chrom: Dict[str, List[Tuple[int, int]]]) -> None:
        self._starts: Dict[str, List[int]] = {}
        self._maxend: Dict[str, List[int]] = {}
        for chrom, ivs in intervals_by_chrom.items():
            ivs_sorted = sorted(ivs)
            starts = [s for s, _ in ivs_sorted]
            maxend: List[int] = []
            running = -1
            for _s, e in ivs_sorted:
                running = max(running, e)
                maxend.append(running)
            self._starts[_strip_chr(chrom)] = starts
            self._maxend[_strip_chr(chrom)] = maxend

    @classmethod
    def empty(cls) -> "RoCCSet":
        return cls({})

    def contains(self, chrom: str, pos_hg38: int) -> bool:
        """Return True if 1-based ``pos_hg38`` lies in any RoCC interval."""
        key = _strip_chr(chrom)
        starts = self._starts.get(key)
        if not starts:
            return False
        pos0 = pos_hg38 - 1  # 0-based coordinate of the queried base
        # Largest interval index whose start <= pos0.
        idx = bisect_right(starts, pos0) - 1
        if idx < 0:
            return False
        # If any interval up to idx reaches past pos0, we're inside one.
        return self._maxend[key][idx] > pos0


def load_roccs(bed_path: Optional[str | Path]) -> RoCCSet:
    """Load a RoCC BED (optionally gzipped) into a :class:`RoCCSet`.

    Returns an empty set if ``bed_path`` is ``None`` (mock path). BED is 0-based
    half-open; columns 1-3 are chrom/start/end.
    """
    if bed_path is None:
        return RoCCSet.empty()
    path = Path(bed_path)
    if not path.exists():
        raise FileNotFoundError(f"RoCC BED not found: {path}")

    opener = gzip.open if path.suffix == ".gz" else open
    by_chrom: Dict[str, List[Tuple[int, int]]] = {}
    with opener(path, "rt") as fh:
        for line in fh:
            if not line.strip() or line.startswith(("#", "track", "browser")):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            chrom, start, end = parts[0], int(parts[1]), int(parts[2])
            by_chrom.setdefault(_strip_chr(chrom), []).append((start, end))
    return RoCCSet(by_chrom)


# --------------------------------------------------------------------------- #
# Main annotation entry point
# --------------------------------------------------------------------------- #
def annotate_constraint(
    df: pd.DataFrame,
    *,
    bigwig_path: Optional[str | Path] = None,
    rocc_bed: Optional[str | Path] = None,
    scorer: Optional[PhyloPScorer] = None,
    rocc_set: Optional[RoCCSet] = None,
    threshold: float = PHYLOP_CONSTRAINED_THRESHOLD,
    mock: bool = False,
) -> pd.DataFrame:
    """Populate ``phylop_241``, ``constrained`` and ``rocc`` in place (copy).

    Parameters
    ----------
    df:
        Canonical substitution table (needs ``chrom`` and ``pos_hg38``).
    bigwig_path:
        Path to ``hg38.cactus241way.phyloP.bw``. Ignored if ``scorer`` given or
        ``mock=True``.
    rocc_bed:
        Path to ``RoCCs.bed.gz``. Ignored if ``rocc_set`` given or ``mock=True``.
    scorer:
        Explicit :class:`PhyloPScorer` (dependency injection for tests).
    rocc_set:
        Explicit :class:`RoCCSet` (dependency injection for tests).
    threshold:
        phyloP cutoff for ``constrained`` (default 2.27, project-locked).
    mock:
        If ``True`` and no explicit scorer/rocc_set given, use
        :class:`MockPhyloPScorer` and an empty RoCC set -- no downloads.

    Returns
    -------
    A schema-valid copy of ``df`` with the three constraint columns filled.
    """
    out = df.copy()

    if scorer is None:
        if mock or bigwig_path is None:
            scorer = MockPhyloPScorer()
        else:
            scorer = BigWigPhyloPScorer(bigwig_path)

    if rocc_set is None:
        rocc_set = RoCCSet.empty() if (mock or rocc_bed is None) else load_roccs(rocc_bed)

    phylop_vals: List[float] = []
    rocc_flags: List[bool] = []
    for chrom, pos in zip(out["chrom"].astype(str), out["pos_hg38"].astype(int)):
        score = scorer.score(chrom, int(pos))
        phylop_vals.append(score)
        rocc_flags.append(rocc_set.contains(chrom, int(pos)))

    phylop_arr = np.asarray(phylop_vals, dtype="float64")
    out["phylop_241"] = phylop_arr
    # nan-safe: NaN > threshold is False, so unscored bases are "not constrained".
    out["constrained"] = np.where(np.isnan(phylop_arr), False, phylop_arr > threshold)
    out["rocc"] = np.asarray(rocc_flags, dtype="bool")

    out = coerce(out)
    return validate(out)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _strip_chr(chrom: str) -> str:
    return chrom[3:] if chrom.startswith("chr") else chrom


def _match_chrom(chrom: str, available: Dict[str, int]) -> Optional[str]:
    """Return the key in ``available`` matching ``chrom`` with/without 'chr'."""
    if chrom in available:
        return chrom
    alt = _strip_chr(chrom)
    if alt in available:
        return alt
    withchr = f"chr{alt}"
    if withchr in available:
        return withchr
    return None
