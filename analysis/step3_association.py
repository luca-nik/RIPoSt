"""
Step 3 — Association analysis: CSED+ vs CSED− (RIPoSt_SV binary).

  - Continuous predictors: Mann-Whitney U + rank-biserial correlation (effect size)
  - Binary/categorical predictors: Chi-square (or Fisher's exact) + Cramér's V

Outputs:
  - Forest-style bar chart of effect sizes per predictor group.
  - CSV with all statistics.
"""
import numpy as np
import pandas as pd
from scipy import stats

from .config import OUTCOME_SV, PREDICTOR_GROUPS, ALPHA
from .utils import (
    ensure_output_dir, save_fig, make_bar_chart,
    check_readability, significance_stars, sample_label,
)

STEP = "step3_association"


def _rank_biserial(x_pos, x_neg) -> float:
    """
    Rank-biserial correlation as effect size for Mann-Whitney U.
    Positive r → CSED+ group has higher values.
    Negative r → CSED− group has higher values.
    """
    n1, n2 = len(x_pos), len(x_neg)
    if n1 == 0 or n2 == 0:
        return np.nan
    u1, _ = stats.mannwhitneyu(x_pos, x_neg, alternative="two-sided")
    u2 = n1 * n2 - u1
    r = (u1 - u2) / (n1 * n2)
    return r


def _cramers_v(contingency) -> float:
    """Cramér's V effect size for chi-square."""
    chi2, _, _, _ = stats.chi2_contingency(contingency, correction=False)
    n = contingency.sum().sum()
    k = min(contingency.shape) - 1
    if n == 0 or k == 0:
        return np.nan
    return np.sqrt(chi2 / (n * k))


def _test_predictor(
    series: pd.Series, outcome: pd.Series
) -> dict:
    """
    Choose the appropriate test based on variable type.
    Returns a dict with effect_size, p_value, n, test_type.
    """
    mask = series.notna() & outcome.notna()
    x = series[mask]
    y = outcome[mask]  # 0/1
    n = mask.sum()

    if n < 10:
        return {"effect_size": np.nan, "p_value": np.nan, "n": n, "test": "insufficient data"}

    # Determine if binary/categorical (≤5 unique values) or continuous
    n_unique = x.nunique()

    if n_unique <= 5:
        # Chi-square / Fisher's exact
        try:
            ct = pd.crosstab(x, y)
            if ct.shape == (2, 2):
                _, p, _, _ = stats.chi2_contingency(ct, correction=True)
                # Fisher if expected < 5
                expected = stats.contingency.expected_freq(ct)
                if (expected < 5).any():
                    _, p = stats.fisher_exact(ct)
                    test = "Fisher"
                else:
                    test = "Chi-square"
            else:
                _, p, _, _ = stats.chi2_contingency(ct)
                test = "Chi-square"
            es = _cramers_v(ct)
            return {"effect_size": es, "p_value": p, "n": n, "test": test}
        except Exception:
            return {"effect_size": np.nan, "p_value": np.nan, "n": n, "test": "error"}
    else:
        # Mann-Whitney U
        pos = x[y == 1].values
        neg = x[y == 0].values
        if len(pos) < 3 or len(neg) < 3:
            return {"effect_size": np.nan, "p_value": np.nan, "n": n, "test": "insufficient groups"}
        try:
            _, p = stats.mannwhitneyu(pos, neg, alternative="two-sided")
            es = _rank_biserial(pos, neg)
            return {"effect_size": es, "p_value": p, "n": n, "test": "Mann-Whitney"}
        except Exception:
            return {"effect_size": np.nan, "p_value": np.nan, "n": n, "test": "error"}


def run(df: pd.DataFrame, predictors: list[str], sample: str) -> pd.DataFrame:
    """
    Run Step 3 for a given sample dataframe.
    Returns full results DataFrame.
    """
    print(f"\n── Step 3: Association analysis (CSED+/−) [{sample_label(sample)}]")

    out_dir = ensure_output_dir(sample, STEP)

    if OUTCOME_SV not in df.columns:
        print(f"  ERROR: outcome column '{OUTCOME_SV}' not found.")
        return pd.DataFrame()

    outcome = df[OUTCOME_SV]
    valid_preds = [c for c in predictors if c in df.columns]

    rows = []
    for col in valid_preds:
        res = _test_predictor(df[col], outcome)
        res["variable"] = col
        rows.append(res)

    results = pd.DataFrame(rows)

    # Save CSV
    results.sort_values("p_value").to_csv(out_dir / "association_results.csv", index=False)

    # Print top results
    sig = results[results["p_value"] < ALPHA].sort_values("effect_size", key=abs, ascending=False)
    print(f"\n  Top significant associations (p<{ALPHA}):")
    if sig.empty:
        print("  None found.")
    else:
        for _, row in sig.head(10).iterrows():
            print(
                f"    {row['variable']:<35} ES={row['effect_size']:+.3f}  "
                f"p={row['p_value']:.4f}{significance_stars(row['p_value'])}  "
                f"n={int(row['n'])}  [{row['test']}]"
            )

    # Plot per group
    for group_name, group_cols in PREDICTOR_GROUPS.items():
        # Include encoded variants
        expanded = []
        for c in group_cols:
            if c in results["variable"].values:
                expanded.append(c)
            else:
                encoded = [v for v in results["variable"].values if v.startswith(c + "_")]
                expanded.extend(encoded)

        sub = results[results["variable"].isin(expanded)].dropna(subset=["effect_size"])
        if sub.empty:
            continue

        n_vars = len(sub)
        check_readability(n_vars, f"Association [{group_name}] — {sample_label(sample)}")

        fig = make_bar_chart(
            labels=sub["variable"].tolist(),
            values=sub["effect_size"].tolist(),
            errors=None,
            title=(
                f"Effect sizes vs CSED (RIPoSt-SV)\n"
                f"{group_name} — {sample_label(sample)}\n"
                f"Cramér's V (categorical) or rank-biserial r (continuous)"
            ),
            xlabel="Effect size",
            color_values=sub["p_value"].tolist(),
            vline=0.0,
        )
        filename = f"{group_name.lower().replace(' ', '_')}.png"
        save_fig(fig, out_dir, filename)

    return results
