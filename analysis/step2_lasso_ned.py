"""
Step 2 — LASSO linear regression predicting RIPoSt_NED (continuous).

Outputs:
  - Bar chart of non-zero LASSO coefficients (standardized).
  - CSV with coefficients and cross-validated R² / RMSE.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error

from .config import OUTCOME_NED, ALPHA
from .utils import ensure_output_dir, save_fig, make_bar_chart, sample_label, check_readability

STEP = "step2_lasso_ned"


def run(df: pd.DataFrame, predictors: list[str], sample: str) -> dict:
    """
    Run Step 2 LASSO regression for a given sample.
    Returns dict with model performance metrics.
    """
    print(f"\n── Step 2: LASSO linear regression → {OUTCOME_NED} [{sample_label(sample)}]")

    out_dir = ensure_output_dir(sample, STEP)

    # Keep predictors present in df, drop rows missing the outcome
    valid_preds = [c for c in predictors if c in df.columns]
    data = df[valid_preds + [OUTCOME_NED]].dropna(subset=[OUTCOME_NED])

    # Drop columns with >50% missing (they'd shrink sample too much)
    thresh = len(data) * 0.5
    data = data.dropna(axis=1, thresh=thresh)
    valid_preds = [c for c in valid_preds if c in data.columns]

    # Fill remaining missing with column median (for LASSO, minimal imputation)
    # Note: only within-column median, not cross-variable — avoids leakage
    X = data[valid_preds].apply(lambda col: col.fillna(col.median()))
    y = data[OUTCOME_NED]

    n_samples = len(X)
    n_features = X.shape[1]
    print(f"  N={n_samples}, features={n_features}")

    if n_samples < 30:
        print("  SKIP: fewer than 30 complete cases.")
        return {}

    # Standardize + LASSO with cross-validated alpha selection
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    lasso = LassoCV(cv=5, random_state=42, max_iter=10000)
    lasso.fit(X_scaled, y)

    # Cross-validated R²
    cv_r2 = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("lasso", LassoCV(cv=5, max_iter=10000, random_state=42))]),
        X, y, cv=5, scoring="r2",
    )
    cv_rmse = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("lasso", LassoCV(cv=5, max_iter=10000, random_state=42))]),
        X, y, cv=5, scoring="neg_root_mean_squared_error",
    )

    metrics = {
        "alpha": lasso.alpha_,
        "cv_r2_mean": cv_r2.mean(),
        "cv_r2_std": cv_r2.std(),
        "cv_rmse_mean": -cv_rmse.mean(),
        "cv_rmse_std": cv_rmse.std(),
        "n": n_samples,
        "n_features": n_features,
    }

    print(f"  Best alpha: {lasso.alpha_:.4f}")
    print(f"  CV R²: {cv_r2.mean():.3f} ± {cv_r2.std():.3f}")
    print(f"  CV RMSE: {-cv_rmse.mean():.2f} ± {cv_rmse.std():.2f}")

    # Extract non-zero coefficients
    coef = pd.Series(lasso.coef_, index=valid_preds)
    nonzero = coef[coef != 0].sort_values(key=abs, ascending=False)

    if nonzero.empty:
        print("  LASSO shrunk all coefficients to zero (strong regularization).")
        return metrics

    print(f"  Non-zero coefficients: {len(nonzero)}/{n_features}")
    for var, c in nonzero.items():
        print(f"    {var:<35} β={c:+.4f}")

    # Save CSV
    coef_df = pd.DataFrame({
        "variable": valid_preds,
        "coefficient": lasso.coef_,
    }).query("coefficient != 0").sort_values("coefficient", key=abs, ascending=False)
    coef_df.to_csv(out_dir / "lasso_coefficients.csv", index=False)

    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(out_dir / "lasso_metrics.csv", index=False)

    # Plot
    n_vars = len(nonzero)
    check_readability(n_vars, f"LASSO coefficients [{sample_label(sample)}]")

    fig = make_bar_chart(
        labels=nonzero.index.tolist(),
        values=nonzero.values.tolist(),
        errors=None,
        title=(
            f"LASSO regression — standardized coefficients\n"
            f"Outcome: RIPoSt-NED | {sample_label(sample)}\n"
            f"CV R²={cv_r2.mean():.2f}±{cv_r2.std():.2f}  α={lasso.alpha_:.4f}  N={n_samples}"
        ),
        xlabel="Standardized β (LASSO)",
        color_values=None,
    )
    save_fig(fig, out_dir, "lasso_coefficients.png")

    return metrics
