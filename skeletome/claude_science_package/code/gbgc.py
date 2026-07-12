"""GC-biased gene conversion (gBGC) classification and flagging.

Pipeline phase P2 (gBGC half) -- a FIRST-CLASS headline arm (project decision #2),
not a footnote. Many HAR substitutions are the signature of gBGC (a recombination-
associated transmission bias that favors Strong (G/C) over Weak (A/T) alleles) and
mimic positive selection without any regulatory function. We separate that noise.

For every substitution we compute, using the ancestral -> derived polarity:

* ``gbgc_class``
    - ``"WtoS"``   : Weak (A/T) ancestral -> Strong (G/C) derived. The gBGC-favored
                     direction; substitutions in high-recombination regions are
                     suspect.
    - ``"StoW"``   : Strong (G/C) -> Weak (A/T). The gBGC-disfavored direction.
    - ``"neutral"``: no change in Weak/Strong class (e.g. A<->T or G<->C, or any
                     substitution that does not cross the W/S boundary).
* ``recomb_rate_cMperMb`` : local recombination rate at the position, joined from a
                            genetic map (e.g. deCODE / HapMap), in cM/Mb.
* ``gbgc_flag``           : ``True`` when the substitution looks like a gBGC
                            artifact: it is ``WtoS`` AND sits in elevated
                            recombination (rate above ``recomb_threshold`` OR
                            within ``hotspot_window_bp`` of a known hotspot).

The permutation null used downstream (phase P4) is matched on recombination rate,
so this column feeds both the flag and the null.

Mock-data path
--------------
Pass ``recomb_map=None`` / ``mock=True`` to :func:`annotate_gbgc` to use a
deterministic in-memory recombination map (no downloads). Real runs supply a
BED-like genetic map and, optionally, a hotspot BED.

Notes on data sources (confirm before a real run)
-------------------------------------------------
* Recombination maps: deCODE 2019 (Halldorsson) or HapMap II. Format here is a
  simple per-interval TSV of ``chrom  start  end  rate_cMperMb`` (0-based half-open).
  TODO confirm the exact column layout of the map you download and remap via
  ``columns=`` if needed.
* Hotspots: optional BED of recombination-hotspot intervals.
"""

from __future__ import annotations

import gzip
from bisect import bisect_right
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from schema import GBGC_CLASSES, coerce, validate

__all__ = [
    "STRONG_BASES",
    "WEAK_BASES",
    "classify_gbgc",
    "RecombinationMap",
    "load_recombination_map",
    "HotspotSet",
    "load_hotspots",
    "annotate_gbgc",
    "DEFAULT_RECOMB_THRESHOLD_CMPERMB",
    "DEFAULT_HOTSPOT_WINDOW_BP",
]

STRONG_BASES = frozenset("GC")
WEAK_BASES = frozenset("AT")

# Defaults for the gBGC flag. A rate well above the genome-average (~1-2 cM/Mb)
# marks elevated recombination; ~10 cM/Mb is a common conservative hotspot-ish
# cutoff. These are tunable and should be sensitivity-checked in phase P4.
DEFAULT_RECOMB_THRESHOLD_CMPERMB: float = 10.0
DEFAULT_HOTSPOT_WINDOW_BP: int = 1_000


def classify_gbgc(ancestral: str, derived: str) -> str:
    """Classify a substitution as ``WtoS`` / ``StoW`` / ``neutral``.

    Uses ancestral -> derived polarity (NOT hg38 ref/alt). Any substitution that
    does not cross the Weak/Strong boundary (A<->T, G<->C) is ``neutral``.

    Raises
    ------
    ValueError
        If either allele is not a single base in {A,C,G,T} or they are equal.
    """
    a = ancestral.strip().upper()
    d = derived.strip().upper()
    if a not in (STRONG_BASES | WEAK_BASES) or d not in (STRONG_BASES | WEAK_BASES):
        raise ValueError(f"alleles must be in A/C/G/T, got {ancestral!r}->{derived!r}")
    if a == d:
        raise ValueError(f"ancestral == derived ({a}); not a substitution")

    a_strong = a in STRONG_BASES
    d_strong = d in STRONG_BASES
    if not a_strong and d_strong:
        return "WtoS"
    if a_strong and not d_strong:
        return "StoW"
    return "neutral"


# --------------------------------------------------------------------------- #
# Recombination map (interval -> rate in cM/Mb)
# --------------------------------------------------------------------------- #
class RecombinationMap:
    """Piecewise-constant recombination rate lookup (0-based half-open intervals).

    Intervals per chromosome are stored sorted by start; a point query binary-
    searches for the containing interval. Positions not covered return ``nan``.
    """

    def __init__(
        self, intervals_by_chrom: Dict[str, List[Tuple[int, int, float]]]
    ) -> None:
        self._starts: Dict[str, List[int]] = {}
        self._ends: Dict[str, List[int]] = {}
        self._rates: Dict[str, List[float]] = {}
        for chrom, ivs in intervals_by_chrom.items():
            key = _strip_chr(chrom)
            ivs_sorted = sorted(ivs)
            self._starts[key] = [s for s, _, _ in ivs_sorted]
            self._ends[key] = [e for _, e, _ in ivs_sorted]
            self._rates[key] = [r for _, _, r in ivs_sorted]

    @classmethod
    def empty(cls) -> "RecombinationMap":
        return cls({})

    def rate(self, chrom: str, pos_hg38: int) -> float:
        """Return cM/Mb at 1-based ``pos_hg38`` (nan if uncovered)."""
        key = _strip_chr(chrom)
        starts = self._starts.get(key)
        if not starts:
            return float("nan")
        pos0 = pos_hg38 - 1
        idx = bisect_right(starts, pos0) - 1
        if idx < 0:
            return float("nan")
        if pos0 < self._ends[key][idx]:
            return self._rates[key][idx]
        return float("nan")


class MockRecombinationMap(RecombinationMap):
    """Deterministic recombination map for the no-download path and tests.

    Returns a stable pseudo-random rate seeded by (chrom, 10kb-bin) so nearby
    positions share a rate, plus an ``overrides`` map to pin rates at specific
    control positions in tests.
    """

    def __init__(
        self, *, overrides: Optional[Dict[Tuple[str, int], float]] = None
    ) -> None:
        super().__init__({})
        self._overrides = dict(overrides or {})

    def rate(self, chrom: str, pos_hg38: int) -> float:
        key = (_strip_chr(chrom), pos_hg38)
        if key in self._overrides:
            return self._overrides[key]
        bin_key = (_strip_chr(chrom), pos_hg38 // 10_000)
        seed = (hash(bin_key) & 0xFFFF) / 0xFFFF  # [0, 1)
        return float(seed * 6.0)  # ~[0, 6) cM/Mb -> mostly below hotspot cutoff


def load_recombination_map(
    path: Optional[str | Path],
    *,
    columns: Optional[Dict[str, str]] = None,
    sep: str = "\t",
    has_header: bool = True,
) -> RecombinationMap:
    """Load a genetic map (``chrom start end rate_cMperMb``) into a map object.

    Returns an empty map if ``path`` is ``None`` (mock path). ``columns`` remaps
    logical names ``chrom/start/end/rate`` to actual headers when ``has_header``.
    When ``has_header`` is False, columns are taken positionally as 0..3.

    TODO confirm the exact layout of the deCODE/HapMap map you download.
    """
    if path is None:
        return RecombinationMap.empty()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"recombination map not found: {p}")

    cols = {"chrom": "chrom", "start": "start", "end": "end", "rate": "rate_cMperMb"}
    cols.update(columns or {})

    opener = gzip.open if p.suffix == ".gz" else open
    by_chrom: Dict[str, List[Tuple[int, int, float]]] = {}
    with opener(p, "rt") as fh:
        header: Optional[List[str]] = None
        for i, line in enumerate(fh):
            if not line.strip() or line.startswith(("#", "track", "browser")):
                continue
            parts = line.rstrip("\n").split(sep)
            if has_header and header is None:
                header = parts
                continue
            if has_header:
                assert header is not None
                rec = dict(zip(header, parts))
                chrom = rec[cols["chrom"]]
                start = int(float(rec[cols["start"]]))
                end = int(float(rec[cols["end"]]))
                rate = float(rec[cols["rate"]])
            else:
                chrom, start, end, rate = (
                    parts[0], int(float(parts[1])), int(float(parts[2])), float(parts[3])
                )
            by_chrom.setdefault(_strip_chr(chrom), []).append((start, end, rate))
    return RecombinationMap(by_chrom)


# --------------------------------------------------------------------------- #
# Recombination hotspots (optional)
# --------------------------------------------------------------------------- #
class HotspotSet:
    """Nearest-hotspot distance lookup over hotspot BED intervals (0-based)."""

    def __init__(self, intervals_by_chrom: Dict[str, List[Tuple[int, int]]]) -> None:
        self._starts: Dict[str, List[int]] = {}
        self._ends: Dict[str, List[int]] = {}
        for chrom, ivs in intervals_by_chrom.items():
            key = _strip_chr(chrom)
            ivs_sorted = sorted(ivs)
            self._starts[key] = [s for s, _ in ivs_sorted]
            self._ends[key] = [e for _, e in ivs_sorted]

    @classmethod
    def empty(cls) -> "HotspotSet":
        return cls({})

    def within(self, chrom: str, pos_hg38: int, window_bp: int) -> bool:
        """Return True if ``pos_hg38`` is within ``window_bp`` of any hotspot."""
        key = _strip_chr(chrom)
        starts = self._starts.get(key)
        if not starts:
            return False
        pos0 = pos_hg38 - 1
        ends = self._ends[key]
        # Candidate interval whose start <= pos0+window; check neighbors for
        # minimal distance (intervals are sorted by start).
        idx = bisect_right(starts, pos0) - 1
        for j in (idx, idx + 1):
            if 0 <= j < len(starts):
                s, e = starts[j], ends[j]
                # distance 0 if inside [s, e); else gap to nearest edge
                if s <= pos0 < e:
                    return True
                dist = s - pos0 if pos0 < s else pos0 - (e - 1)
                if dist <= window_bp:
                    return True
        return False


def load_hotspots(path: Optional[str | Path]) -> HotspotSet:
    """Load a hotspot BED (optionally gzipped). Empty set if ``path`` is None."""
    if path is None:
        return HotspotSet.empty()
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"hotspot BED not found: {p}")
    opener = gzip.open if p.suffix == ".gz" else open
    by_chrom: Dict[str, List[Tuple[int, int]]] = {}
    with opener(p, "rt") as fh:
        for line in fh:
            if not line.strip() or line.startswith(("#", "track", "browser")):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            by_chrom.setdefault(_strip_chr(parts[0]), []).append(
                (int(parts[1]), int(parts[2]))
            )
    return HotspotSet(by_chrom)


# --------------------------------------------------------------------------- #
# Main annotation entry point
# --------------------------------------------------------------------------- #
def annotate_gbgc(
    df: pd.DataFrame,
    *,
    recomb_map: Optional[RecombinationMap] = None,
    recomb_map_path: Optional[str | Path] = None,
    hotspots: Optional[HotspotSet] = None,
    hotspot_bed: Optional[str | Path] = None,
    recomb_threshold: float = DEFAULT_RECOMB_THRESHOLD_CMPERMB,
    hotspot_window_bp: int = DEFAULT_HOTSPOT_WINDOW_BP,
    mock: bool = False,
) -> pd.DataFrame:
    """Populate ``gbgc_class``, ``recomb_rate_cMperMb`` and ``gbgc_flag``.

    Parameters
    ----------
    df:
        Canonical substitution table (needs ``ref_ancestral``, ``alt_human``,
        ``chrom``, ``pos_hg38``).
    recomb_map / recomb_map_path:
        A :class:`RecombinationMap` or a path to load one. If both are ``None``
        and ``mock=True``, a :class:`MockRecombinationMap` is used.
    hotspots / hotspot_bed:
        Optional hotspot set or BED path. Absent -> hotspot proximity contributes
        nothing to the flag.
    recomb_threshold:
        cM/Mb above which recombination is considered "elevated" for the flag.
    hotspot_window_bp:
        Distance to a hotspot that counts as "near a hotspot" for the flag.
    mock:
        Use the deterministic in-memory recombination map when no map is given.

    Returns
    -------
    A schema-valid copy of ``df`` with the three gBGC columns filled.

    Flag semantics
    --------------
    ``gbgc_flag = (gbgc_class == "WtoS") AND (rate > threshold OR near_hotspot)``.
    Only WtoS substitutions can be flagged, because gBGC drives fixation of the
    Strong allele. StoW and neutral substitutions are never flagged.
    """
    out = df.copy()

    if recomb_map is None:
        if mock or recomb_map_path is None:
            recomb_map = MockRecombinationMap()
        else:
            recomb_map = load_recombination_map(recomb_map_path)

    if hotspots is None:
        hotspots = HotspotSet.empty() if (mock or hotspot_bed is None) else load_hotspots(hotspot_bed)

    classes: List[str] = []
    rates: List[float] = []
    flags: List[bool] = []

    for anc, der, chrom, pos in zip(
        out["ref_ancestral"].astype(str),
        out["alt_human"].astype(str),
        out["chrom"].astype(str),
        out["pos_hg38"].astype(int),
    ):
        cls = classify_gbgc(anc, der)
        rate = recomb_map.rate(chrom, int(pos))
        near = hotspots.within(chrom, int(pos), hotspot_window_bp)

        elevated = (not np.isnan(rate)) and (rate > recomb_threshold)
        flag = (cls == "WtoS") and (elevated or near)

        classes.append(cls)
        rates.append(rate)
        flags.append(bool(flag))

    assert set(classes) <= set(GBGC_CLASSES)  # invariant guard
    out["gbgc_class"] = classes
    out["recomb_rate_cMperMb"] = np.asarray(rates, dtype="float64")
    out["gbgc_flag"] = np.asarray(flags, dtype="bool")

    out = coerce(out)
    return validate(out)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _strip_chr(chrom: str) -> str:
    return chrom[3:] if chrom.startswith("chr") else chrom
