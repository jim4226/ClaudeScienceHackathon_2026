"""SKELETOME canonical results schema.

Single source of truth for the one-row-per-substitution results table that every
other module in the pipeline reads from and writes to. The column names, order,
and types defined here MUST match the CANONICAL RESULTS TSV in the project
context exactly -- if you change a column here, you are changing the contract for
the whole pipeline.

The module deliberately avoids a hard dependency on pydantic so it can run in a
bare environment: a lightweight ``dataclass`` carries the row, and ``validate()``
enforces column names + types on a pandas DataFrame. If pydantic is installed a
``RowModel`` is also exposed for callers that want per-field coercion, but it is
optional.

Usage
-----
>>> import pandas as pd
>>> from schema import COLUMNS, empty_frame, validate
>>> df = empty_frame()              # correctly-typed empty table
>>> validate(df)                    # raises SchemaError on any mismatch
>>> list(df.columns) == COLUMNS
True
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

__all__ = [
    "COLUMNS",
    "COLUMN_DTYPES",
    "GBGC_CLASSES",
    "CONTROL_LABELS",
    "PHYLOP_CONSTRAINED_THRESHOLD",
    "SubstitutionRow",
    "SchemaError",
    "empty_frame",
    "validate",
    "coerce",
    "rows_to_frame",
]

# --------------------------------------------------------------------------- #
# Canonical column order. DO NOT reorder or rename without updating the project
# context TSV spec and every consumer module.
# --------------------------------------------------------------------------- #
COLUMNS: List[str] = [
    # --- identity ---------------------------------------------------------- #
    "har_id",
    "chrom",
    "pos_hg38",
    "ref_ancestral",
    "alt_human",
    "target_gene_hypothesis",
    # --- constraint (constraint.py) --------------------------------------- #
    "phylop_241",
    "constrained",
    "rocc",
    # --- gBGC control (gbgc.py) ------------------------------------------- #
    "gbgc_class",
    "recomb_rate_cMperMb",
    "gbgc_flag",
    # --- AlphaGenome (PRIMARY engine) ------------------------------------- #
    "ag_atac_delta",
    "ag_dnase_delta",
    # --- ChromBPNet (OPTIONAL enrichment layer) --------------------------- #
    "cbp_limb_logfc",
    "cbp_msc_logfc",
    "cbp_mg63_logfc",
    "cbp_jsd",
    # --- neural comparator ------------------------------------------------ #
    "neural_delta",
    # --- derived calls ---------------------------------------------------- #
    "skeletal_specific",
    "candidate",
    # --- GWAS supporting annotation --------------------------------------- #
    "oa_credible_overlap",
    "oa_credible_set_id",
    "gwas_enrich_p",
    # --- statistics ------------------------------------------------------- #
    "composite_score",
    "empirical_p",
    "fdr_bh",
    # --- provenance ------------------------------------------------------- #
    "is_control",
    "notes",
]

# Threshold for the Zoonomia 241-way phyloP "constrained" call (project-locked).
PHYLOP_CONSTRAINED_THRESHOLD: float = 2.27

# Allowed categorical vocabularies.
GBGC_CLASSES = ("WtoS", "StoW", "neutral")
CONTROL_LABELS = ("GDF5-GROW1", "GDF5-R4", "HACNS1", "negative", "none")

# --------------------------------------------------------------------------- #
# Column dtype contract. We describe *logical* types; validate() accepts the
# corresponding pandas/numpy dtypes and tolerates NaN in numeric/boolean-nullable
# columns because most columns are populated by later pipeline phases.
# --------------------------------------------------------------------------- #
# Logical type tags: "str", "int", "float", "bool", "category:<name>"
COLUMN_DTYPES: Dict[str, str] = {
    "har_id": "str",
    "chrom": "str",
    "pos_hg38": "int",
    "ref_ancestral": "str",
    "alt_human": "str",
    "target_gene_hypothesis": "str",
    "phylop_241": "float",
    "constrained": "bool",
    "rocc": "bool",
    "gbgc_class": "category:gbgc",
    "recomb_rate_cMperMb": "float",
    "gbgc_flag": "bool",
    "ag_atac_delta": "float",
    "ag_dnase_delta": "float",
    "cbp_limb_logfc": "float",
    "cbp_msc_logfc": "float",
    "cbp_mg63_logfc": "float",
    "cbp_jsd": "float",
    "neural_delta": "float",
    "skeletal_specific": "bool",
    "candidate": "bool",
    "oa_credible_overlap": "bool",
    "oa_credible_set_id": "str",
    "gwas_enrich_p": "float",
    "composite_score": "float",
    "empirical_p": "float",
    "fdr_bh": "float",
    "is_control": "category:control",
    "notes": "str",
}

# Columns that are legitimately populated only in later phases and therefore may
# be entirely null immediately after substitution enumeration.
_LATE_PHASE_COLUMNS = {
    "phylop_241",
    "recomb_rate_cMperMb",
    "ag_atac_delta",
    "ag_dnase_delta",
    "cbp_limb_logfc",
    "cbp_msc_logfc",
    "cbp_mg63_logfc",
    "cbp_jsd",
    "neural_delta",
    "oa_credible_set_id",
    "gwas_enrich_p",
    "composite_score",
    "empirical_p",
    "fdr_bh",
}


class SchemaError(ValueError):
    """Raised when a DataFrame violates the canonical results schema."""


# --------------------------------------------------------------------------- #
# Row dataclass
# --------------------------------------------------------------------------- #
@dataclass
class SubstitutionRow:
    """One human-specific substitution.

    Only the identity + provenance fields are required at construction time; the
    remaining analytical columns default to null/False and are filled by later
    pipeline phases (constraint, gBGC, AlphaGenome, stats). Booleans default to
    ``False`` (a conservative "not called") and float scores default to NaN
    ("not yet computed") so a partially-filled table is unambiguous.
    """

    # identity (required)
    har_id: str
    chrom: str
    pos_hg38: int
    ref_ancestral: str
    alt_human: str
    target_gene_hypothesis: str = ""

    # constraint
    phylop_241: float = float("nan")
    constrained: bool = False
    rocc: bool = False

    # gBGC
    gbgc_class: str = "neutral"
    recomb_rate_cMperMb: float = float("nan")
    gbgc_flag: bool = False

    # AlphaGenome
    ag_atac_delta: float = float("nan")
    ag_dnase_delta: float = float("nan")

    # ChromBPNet (optional)
    cbp_limb_logfc: float = float("nan")
    cbp_msc_logfc: float = float("nan")
    cbp_mg63_logfc: float = float("nan")
    cbp_jsd: float = float("nan")

    # neural comparator
    neural_delta: float = float("nan")

    # derived calls
    skeletal_specific: bool = False
    candidate: bool = False

    # GWAS
    oa_credible_overlap: bool = False
    oa_credible_set_id: str = ""
    gwas_enrich_p: float = float("nan")

    # statistics
    composite_score: float = float("nan")
    empirical_p: float = float("nan")
    fdr_bh: float = float("nan")

    # provenance
    is_control: str = "none"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.gbgc_class not in GBGC_CLASSES:
            raise SchemaError(
                f"gbgc_class must be one of {GBGC_CLASSES}, got {self.gbgc_class!r}"
            )
        if self.is_control not in CONTROL_LABELS:
            raise SchemaError(
                f"is_control must be one of {CONTROL_LABELS}, got {self.is_control!r}"
            )
        self.pos_hg38 = int(self.pos_hg38)

    def to_dict(self) -> Dict[str, Any]:
        """Return an ordered dict keyed by the canonical column names."""
        raw = {f.name: getattr(self, f.name) for f in fields(self)}
        return {col: raw[col] for col in COLUMNS}


# Fail fast at import time if the dataclass and COLUMNS ever drift apart.
_dataclass_field_names = {f.name for f in fields(SubstitutionRow)}
if _dataclass_field_names != set(COLUMNS):
    missing = set(COLUMNS) - _dataclass_field_names
    extra = _dataclass_field_names - set(COLUMNS)
    raise SchemaError(
        "SubstitutionRow fields drifted from COLUMNS. "
        f"missing={sorted(missing)} extra={sorted(extra)}"
    )


# --------------------------------------------------------------------------- #
# Frame constructors + validation
# --------------------------------------------------------------------------- #
def empty_frame() -> pd.DataFrame:
    """Return an empty DataFrame with all canonical columns and correct dtypes."""
    return coerce(pd.DataFrame({c: [] for c in COLUMNS}))


def rows_to_frame(rows: List[SubstitutionRow]) -> pd.DataFrame:
    """Build a fully-typed DataFrame from a list of :class:`SubstitutionRow`."""
    if not rows:
        return empty_frame()
    df = pd.DataFrame([r.to_dict() for r in rows], columns=COLUMNS)
    return coerce(df)


def coerce(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a DataFrame's columns to the canonical dtypes.

    Adds any missing columns with null/default values, drops nothing, and returns
    the columns in canonical order. This is the recommended way to normalize a
    table produced by an ad-hoc step before handing it to the next phase.
    """
    df = df.copy()

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = _default_series(col, len(df))

    df = df[COLUMNS]  # canonical order; raises KeyError if a column is missing

    for col, logical in COLUMN_DTYPES.items():
        df[col] = _coerce_series(df[col], logical)
    return df


def _default_series(col: str, n: int) -> pd.Series:
    logical = COLUMN_DTYPES[col]
    if logical == "str":
        return pd.Series([""] * n, dtype="object")
    if logical == "int":
        return pd.Series([0] * n, dtype="int64")
    if logical == "float":
        return pd.Series([np.nan] * n, dtype="float64")
    if logical == "bool":
        return pd.Series([False] * n, dtype="bool")
    if logical == "category:gbgc":
        return pd.Series(["neutral"] * n, dtype="object")
    if logical == "category:control":
        return pd.Series(["none"] * n, dtype="object")
    raise SchemaError(f"unknown logical type {logical!r} for column {col!r}")


def _coerce_series(s: pd.Series, logical: str) -> pd.Series:
    if logical == "str":
        return s.fillna("").astype("object").map(lambda x: "" if x is None else str(x))
    if logical == "int":
        # positions are always concrete integers; do not allow NaN here
        return pd.to_numeric(s, errors="raise").astype("int64")
    if logical == "float":
        return pd.to_numeric(s, errors="coerce").astype("float64")
    if logical == "bool":
        return s.fillna(False).astype("bool")
    if logical == "category:gbgc":
        return _coerce_categorical(s, GBGC_CLASSES, default="neutral")
    if logical == "category:control":
        return _coerce_categorical(s, CONTROL_LABELS, default="none")
    raise SchemaError(f"unknown logical type {logical!r}")


def _coerce_categorical(s: pd.Series, allowed: tuple, default: str) -> pd.Series:
    out = s.fillna(default).astype("object").map(lambda x: default if x is None else str(x))
    bad = set(out.unique()) - set(allowed)
    if bad:
        raise SchemaError(f"illegal categorical values {sorted(bad)}; allowed={allowed}")
    return out


def validate(df: pd.DataFrame, *, require_late_phase: bool = False) -> pd.DataFrame:
    """Validate a DataFrame against the canonical schema.

    Parameters
    ----------
    df:
        Table to validate.
    require_late_phase:
        If ``True``, require that late-phase columns (phyloP, AlphaGenome deltas,
        stats, ...) are non-null. Default ``False`` so that tables emitted right
        after substitution enumeration -- before scoring -- still validate.

    Returns
    -------
    The same DataFrame (unchanged) so ``validate`` can be used inline.

    Raises
    ------
    SchemaError
        On any column-name, ordering, dtype, or categorical-vocabulary violation.
    """
    actual = list(df.columns)
    if actual != COLUMNS:
        missing = [c for c in COLUMNS if c not in actual]
        extra = [c for c in actual if c not in COLUMNS]
        raise SchemaError(
            "column set/order mismatch. "
            f"missing={missing} extra={extra} "
            f"(expected canonical order of {len(COLUMNS)} columns)"
        )

    for col, logical in COLUMN_DTYPES.items():
        _validate_series(df[col], col, logical)

    # Identity columns must always be fully populated.
    for col in ("har_id", "chrom", "pos_hg38", "ref_ancestral", "alt_human"):
        if df[col].isna().any():
            raise SchemaError(f"identity column {col!r} contains null values")
        # String identity columns must also be non-empty (pos_hg38 is integer).
        if col != "pos_hg38" and (df[col].astype(str) == "").any():
            raise SchemaError(f"identity column {col!r} contains empty values")

    for col in ("ref_ancestral", "alt_human"):
        bad = df[~df[col].astype(str).str.upper().isin(list("ACGT"))]
        if len(bad):
            raise SchemaError(
                f"{col!r} must be a single base in {{A,C,G,T}}; "
                f"offending values: {sorted(bad[col].unique())}"
            )

    if require_late_phase:
        for col in _LATE_PHASE_COLUMNS:
            if COLUMN_DTYPES[col] == "float" and df[col].isna().any():
                raise SchemaError(
                    f"late-phase column {col!r} still has null values but "
                    "require_late_phase=True"
                )
    return df


def _validate_series(s: pd.Series, col: str, logical: str) -> None:
    if logical == "int":
        if not pd.api.types.is_integer_dtype(s):
            raise SchemaError(f"{col!r} must be integer dtype, got {s.dtype}")
    elif logical == "float":
        if not pd.api.types.is_float_dtype(s):
            raise SchemaError(f"{col!r} must be float dtype, got {s.dtype}")
    elif logical == "bool":
        if not pd.api.types.is_bool_dtype(s):
            raise SchemaError(f"{col!r} must be bool dtype, got {s.dtype}")
    elif logical == "str":
        if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
            raise SchemaError(f"{col!r} must be string/object dtype, got {s.dtype}")
    elif logical == "category:gbgc":
        bad = set(s.dropna().unique()) - set(GBGC_CLASSES)
        if bad:
            raise SchemaError(f"{col!r} has illegal values {sorted(bad)}")
    elif logical == "category:control":
        bad = set(s.dropna().unique()) - set(CONTROL_LABELS)
        if bad:
            raise SchemaError(f"{col!r} has illegal values {sorted(bad)}")
    else:
        raise SchemaError(f"unknown logical type {logical!r} for {col!r}")


# Optional pydantic mirror -------------------------------------------------- #
try:  # pragma: no cover - exercised only when pydantic is installed
    from pydantic import BaseModel, Field, field_validator

    class RowModel(BaseModel):
        """Optional pydantic view of a row for callers that want field coercion."""

        har_id: str
        chrom: str
        pos_hg38: int
        ref_ancestral: str
        alt_human: str
        target_gene_hypothesis: str = ""
        phylop_241: Optional[float] = None
        constrained: bool = False
        rocc: bool = False
        gbgc_class: str = "neutral"
        recomb_rate_cMperMb: Optional[float] = None
        gbgc_flag: bool = False
        ag_atac_delta: Optional[float] = None
        ag_dnase_delta: Optional[float] = None
        cbp_limb_logfc: Optional[float] = None
        cbp_msc_logfc: Optional[float] = None
        cbp_mg63_logfc: Optional[float] = None
        cbp_jsd: Optional[float] = None
        neural_delta: Optional[float] = None
        skeletal_specific: bool = False
        candidate: bool = False
        oa_credible_overlap: bool = False
        oa_credible_set_id: str = ""
        gwas_enrich_p: Optional[float] = None
        composite_score: Optional[float] = None
        empirical_p: Optional[float] = None
        fdr_bh: Optional[float] = None
        is_control: str = "none"
        notes: str = ""

        @field_validator("gbgc_class")
        @classmethod
        def _chk_gbgc(cls, v: str) -> str:
            if v not in GBGC_CLASSES:
                raise ValueError(f"gbgc_class must be one of {GBGC_CLASSES}")
            return v

        @field_validator("is_control")
        @classmethod
        def _chk_control(cls, v: str) -> str:
            if v not in CONTROL_LABELS:
                raise ValueError(f"is_control must be one of {CONTROL_LABELS}")
            return v

    __all__.append("RowModel")
except ImportError:  # pragma: no cover
    RowModel = None  # type: ignore[assignment]
