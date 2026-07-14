"""Deterministic balance-sensitivity analysis for the LEMON T1 dispersion result.

This script uses only the released derived-feature table. It does not read raw MRI
or controlled data. The four views are oriented so larger values are older-appearing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


SEED = 20260713
N_DRAWS = 5000


def dispersion(z: np.ndarray) -> np.ndarray:
    """Within-person population SD across the four oriented views."""
    return z.std(axis=1, ddof=0)


def effect_summary(d: np.ndarray, older: np.ndarray) -> dict[str, float]:
    young_values = d[~older]
    older_values = d[older]
    difference = older_values.mean() - young_values.mean()
    pooled_sd = np.sqrt(
        (
            (len(young_values) - 1) * young_values.var(ddof=1)
            + (len(older_values) - 1) * older_values.var(ddof=1)
        )
        / (len(d) - 2)
    )
    return {
        "young_mean": float(young_values.mean()),
        "older_mean": float(older_values.mean()),
        "difference": float(difference),
        "cohens_d": float(difference / pooled_sd),
        "mann_whitney_p": float(
            stats.mannwhitneyu(older_values, young_values, alternative="two-sided").pvalue
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    older = frame["group"].eq("older").to_numpy()
    young = ~older
    x = np.column_stack(
        [
            frame["brain_age"].to_numpy(),
            -frame["gm_fraction"].to_numpy(),
            frame["ventricle_brain_ratio"].to_numpy(),
            -frame["brain_tissue_fraction"].to_numpy(),
        ]
    )

    global_z = (x - x.mean(axis=0)) / x.std(axis=0, ddof=0)

    balanced_mean = (x[young].mean(axis=0) + x[older].mean(axis=0)) / 2
    balanced_variance = (
        ((x[young] - balanced_mean) ** 2).mean(axis=0)
        + ((x[older] - balanced_mean) ** 2).mean(axis=0)
    ) / 2
    balanced_z = (x - balanced_mean) / np.sqrt(balanced_variance)

    young_mean = x[young].mean(axis=0)
    young_sd = x[young].std(axis=0, ddof=0)
    young_reference_z = (x - young_mean) / young_sd

    within_group_z = np.empty_like(x)
    for mask in (young, older):
        within_group_z[mask] = (
            x[mask] - x[mask].mean(axis=0)
        ) / x[mask].std(axis=0, ddof=0)

    design = np.column_stack([np.ones(len(frame)), frame["age_mid"].to_numpy()])
    residuals = np.empty_like(x)
    for column in range(x.shape[1]):
        beta = np.linalg.lstsq(design, x[:, column], rcond=None)[0]
        residuals[:, column] = x[:, column] - design @ beta
    residual_z = (residuals - residuals.mean(axis=0)) / residuals.std(axis=0, ddof=0)

    rng = np.random.default_rng(SEED)
    young_indices = np.flatnonzero(young)
    older_indices = np.flatnonzero(older)
    draw_differences: list[float] = []
    draw_effects: list[float] = []
    for _ in range(N_DRAWS):
        selected_young = rng.choice(young_indices, len(older_indices), replace=False)
        selected = np.concatenate([selected_young, older_indices])
        draw_x = x[selected]
        draw_older = np.concatenate(
            [np.zeros(len(older_indices), dtype=bool), np.ones(len(older_indices), dtype=bool)]
        )
        draw_z = (draw_x - draw_x.mean(axis=0)) / draw_x.std(axis=0, ddof=0)
        summary = effect_summary(dispersion(draw_z), draw_older)
        draw_differences.append(summary["difference"])
        draw_effects.append(summary["cohens_d"])

    output = {
        "analysis": "LEMON balanced-group sensitivity",
        "input_rows": int(len(frame)),
        "group_counts": {
            "young": int(young.sum()),
            "older": int(older.sum()),
        },
        "seed": SEED,
        "balanced_subsampling_draws": N_DRAWS,
        "global_scaling": effect_summary(dispersion(global_z), older),
        "equal_group_weight_scaling": effect_summary(dispersion(balanced_z), older),
        "young_reference_scaling": effect_summary(dispersion(young_reference_z), older),
        "linear_age_residual_diagnostic": effect_summary(dispersion(residual_z), older),
        "within_group_scaling_diagnostic": effect_summary(dispersion(within_group_z), older),
        "balanced_69_vs_69_subsampling": {
            "difference_median": float(np.median(draw_differences)),
            "difference_2_5_percentile": float(np.quantile(draw_differences, 0.025)),
            "difference_97_5_percentile": float(np.quantile(draw_differences, 0.975)),
            "cohens_d_median": float(np.median(draw_effects)),
            "cohens_d_2_5_percentile": float(np.quantile(draw_effects, 0.025)),
            "cohens_d_97_5_percentile": float(np.quantile(draw_effects, 0.975)),
            "fraction_positive": float(np.mean(np.asarray(draw_differences) > 0)),
        },
        "interpretation": (
            "The older-younger contrast persists after equal group weighting and balanced "
            "subsampling, but it is attenuated. The within-group standardization diagnostic "
            "does not support excess older-group dispersion after removing each group's "
            "mean profile and marginal scale. The defensible claim is therefore a nonuniform "
            "between-group shift across T1-derived views, not unexplained within-group "
            "biological disorganization."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
