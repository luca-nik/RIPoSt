"""
Step 1 — Spearman correlation of all predictors with RIPoSt_NED (continuous).

Outputs:
  - One horizontal bar chart per predictor group (Demographics, Clinical,
    Scale totals, Scale subscales), sorted by |rho|, colored by significance.
  - A CSV with all rho, p-values, and N for every predictor.
"""
import numpy as np
import pandas as pd
from scipy import stats

from .config import OUTCOME_NED, PREDICTOR_GROUPS, ALPHA
from .utils import (
    ensure_output_dir, save_fig, check_readability,
    make_bar_chart, sample_label,
)


STEP = "step1_spearman"


def _spearman_with_outcome(
    df: pd.DataFrame,
    predictors: list[str],
    outcome: str,
) -> pd.DataFrame:
    """
    Compute Spearman rho between each predictor and the outcome.
    Uses available-case analysis (pairwise non-null).
    Returns a DataFrame with columns: variable, rho, p_value, n.
    """
    rows = []
    y = df[outcome]

    for col in predictors:
        x = df[col]
        # Pairwise complete cases
        mask = x.notna() & y.notna()
        n = mask.sum()
        if n < 10:
            # Too few observations to be meaningful
            rows.append({"variable": col, "rho": np.nan, "p_value": np.nan, "n": n})
            continue
        rho, p = stats.spearmanr(x[mask], y[mask])
        rows.append({"variable": col, "rho": rho, "p_value": p, "n": n})

    return pd.DataFrame(rows)


def _plot_group(
    results: pd.DataFrame,
    group_name: str,
    group_cols: list[str],
    sample: str,
    out_dir,
) -> None:
    """Plot a bar chart for a single predictor group."""
    # Keep only columns that exist in results
    sub = results[results["variable"].isin(group_cols)].dropna(subset=["rho"])
    if sub.empty:
        print(f"  [{group_name}] No data to plot.")
        return

    n_vars = len(sub)
    plot_name = f"{group_name} — {sample_label(sample)}"
    check_readability(n_vars, plot_name)

    fig = make_bar_chart(
        labels=sub["variable"].tolist(),
        values=sub["rho"].tolist(),
        errors=None,
        title=f"Spearman ρ with RIPoSt-NED\n{group_name} — {sample_label(sample)}",
        xlabel="Spearman ρ",
        color_values=sub["p_value"].tolist(),
    )

    # Annotate N on each bar
    ax = fig.axes[0]
    for i, (_, row) in enumerate(
        sub.assign(_abs=sub["rho"].abs()).sort_values("_abs", ascending=False).iterrows()
    ):
        ax.text(
            0.01, i, f"n={int(row['n'])}",
            va="center", ha="left", fontsize=6.5, color="white",
            transform=ax.get_yaxis_transform(),
        )

    filename = f"{group_name.lower().replace(' ', '_')}.png"
    save_fig(fig, out_dir, filename)


def run(df: pd.DataFrame, predictors: list[str], sample: str) -> pd.DataFrame:
    """
    Run Step 1 for a given sample dataframe.
    Returns the full results DataFrame.
    """
    print(f"\n── Step 1: Spearman correlation with {OUTCOME_NED} [{sample_label(sample)}]")

    if OUTCOME_NED not in df.columns:
        print(f"  ERROR: outcome column '{OUTCOME_NED}' not found.")
        return pd.DataFrame()

    out_dir = ensure_output_dir(sample, STEP)

    # Filter predictors to those actually in df
    valid_preds = [c for c in predictors if c in df.columns]

    results = _spearman_with_outcome(df, valid_preds, OUTCOME_NED)

    # Save CSV
    csv_path = out_dir / "spearman_results.csv"
    results.sort_values("p_value").to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path.relative_to(out_dir.parent.parent.parent)}")

    # Plot by group
    for group_name, group_cols in PREDICTOR_GROUPS.items():
        # Map encoded column names: e.g. marital_* and mood_* expansions
        # Include columns that start with the group prefix after encoding
        expanded = []
        for c in group_cols:
            if c in results["variable"].values:
                expanded.append(c)
            else:
                # Check for one-hot encoded versions
                encoded = [v for v in results["variable"].values if v.startswith(c + "_") or v == c]
                expanded.extend(encoded)
        _plot_group(results, group_name, expanded, sample, out_dir)

    # Summary: top 10 significant
    sig = results[results["p_value"] < ALPHA].sort_values("rho", key=abs, ascending=False)
    print(f"\n  Top significant predictors (p<{ALPHA}):")
    if sig.empty:
        print("  None found.")
    else:
        for _, row in sig.head(10).iterrows():
            stars = "***" if row["p_value"] < 0.001 else ("**" if row["p_value"] < 0.01 else "*")
            print(f"    {row['variable']:<35} rho={row['rho']:+.3f}  p={row['p_value']:.4f} {stars}  n={int(row['n'])}")

    return results
