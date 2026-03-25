"""
Step 4 — LASSO logistic regression predicting RIPoSt_SV (CSED binary).

Uses LogisticRegressionCV (L1, liblinear solver) which internally performs
cross-validated C selection. The CV scores are extracted directly from the
fitted model to avoid slow nested cross-validation.

Outputs:
  - Bar chart of non-zero odds ratios (exp(β)).
  - CSV with coefficients, odds ratios, and CV performance (AUC, accuracy).
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from .config import OUTCOME_SV, ALPHA
from .utils import ensure_output_dir, save_fig, make_bar_chart, check_readability, sample_label

STEP = "step4_logistic"


def run(df: pd.DataFrame, predictors: list[str], sample: str) -> dict:
    """
    Run Step 4 LASSO logistic regression for a given sample.
    Returns dict with performance metrics.
    """
    print(f"\n── Step 4: LASSO logistic regression → {OUTCOME_SV} [{sample_label(sample)}]")

    out_dir = ensure_output_dir(sample, STEP)

    valid_preds = [c for c in predictors if c in df.columns]
    data = df[valid_preds + [OUTCOME_SV]].dropna(subset=[OUTCOME_SV])

    # Drop columns with >50% missing
    thresh = len(data) * 0.5
    data = data.dropna(axis=1, thresh=thresh)
    valid_preds = [c for c in valid_preds if c in data.columns]

    # Fill remaining missing with column median
    X_raw = data[valid_preds].apply(lambda col: col.fillna(col.median()))
    y = data[OUTCOME_SV].astype(int)

    n_samples = len(X_raw)
    n_pos = int(y.sum())
    n_neg = int((1 - y).sum())
    print(f"  N={n_samples}  CSED+={n_pos}  CSED−={n_neg}  features={X_raw.shape[1]}")

    if n_samples < 30 or n_pos < 10 or n_neg < 10:
        print("  SKIP: insufficient sample size or class imbalance.")
        return {}

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # L1 logistic with CV-selected C (liblinear is fast for L1, small N)
    clf = LogisticRegressionCV(
        Cs=10, cv=cv, penalty="l1", solver="liblinear",
        max_iter=1000, random_state=42, scoring="roc_auc",
    )
    clf.fit(X_scaled, y)

    best_C = float(clf.C_[0])

    # CV AUC scores stored internally in clf.scores_ (shape: Cs × folds)
    # scores_[1] = AUC scores for class 1, shape (n_folds, n_Cs)
    best_C_idx = np.argmin(np.abs(clf.Cs_ - best_C))
    cv_auc_scores = clf.scores_[1][:, best_C_idx]
    cv_auc_mean = cv_auc_scores.mean()
    cv_auc_std  = cv_auc_scores.std()

    # Accuracy via a simple fixed-C logistic (reuse best_C, fast)
    from sklearn.linear_model import LogisticRegression
    fixed_clf = LogisticRegression(
        C=best_C, penalty="l1", solver="liblinear", max_iter=1000, random_state=42
    )
    cv_acc_scores = cross_val_score(
        Pipeline([("s", StandardScaler()), ("c", fixed_clf)]),
        X_raw, y, cv=cv, scoring="accuracy",
    )
    cv_acc_mean = cv_acc_scores.mean()
    cv_acc_std  = cv_acc_scores.std()

    metrics = {
        "best_C": best_C,
        "cv_auc_mean": cv_auc_mean,
        "cv_auc_std": cv_auc_std,
        "cv_acc_mean": cv_acc_mean,
        "cv_acc_std": cv_acc_std,
        "n": n_samples,
        "n_pos": n_pos,
        "n_neg": n_neg,
    }

    print(f"  Best C: {best_C:.4f}")
    print(f"  CV AUC:      {cv_auc_mean:.3f} ± {cv_auc_std:.3f}")
    print(f"  CV Accuracy: {cv_acc_mean:.3f} ± {cv_acc_std:.3f}")
    print(f"  RIPoSt-SV reference accuracy (paper): ~83%")

    # Extract non-zero coefficients
    coef = pd.Series(clf.coef_[0], index=valid_preds)
    nonzero = coef[coef != 0].sort_values(key=abs, ascending=False)

    if nonzero.empty:
        print("  LASSO shrunk all coefficients to zero.")
        pd.DataFrame([metrics]).to_csv(out_dir / "logistic_metrics.csv", index=False)
        return metrics

    odds_ratios = np.exp(nonzero)
    print(f"  Non-zero coefficients: {len(nonzero)}/{X_raw.shape[1]}")
    for var, (beta, OR) in zip(nonzero.index, zip(nonzero.values, odds_ratios.values)):
        print(f"    {var:<35} β={beta:+.4f}  OR={OR:.3f}")

    # Save CSV
    coef_df = pd.DataFrame({
        "variable": nonzero.index,
        "coefficient": nonzero.values,
        "odds_ratio": odds_ratios.values,
    })
    coef_df.to_csv(out_dir / "logistic_coefficients.csv", index=False)
    pd.DataFrame([metrics]).to_csv(out_dir / "logistic_metrics.csv", index=False)

    # Plot
    n_vars = len(nonzero)
    check_readability(n_vars, f"Logistic LASSO [{sample_label(sample)}]")

    fig = make_bar_chart(
        labels=[f"{v}  (OR={or_:.2f})" for v, or_ in zip(nonzero.index, odds_ratios)],
        values=nonzero.values.tolist(),
        errors=None,
        title=(
            f"LASSO logistic regression — standardized β\n"
            f"Outcome: CSED (RIPoSt-SV) | {sample_label(sample)}\n"
            f"CV AUC={cv_auc_mean:.2f}±{cv_auc_std:.2f}  "
            f"Acc={cv_acc_mean:.2f}±{cv_acc_std:.2f}  N={n_samples}"
        ),
        xlabel="Standardized β  (OR = exp(β), shown in label)",
        color_values=None,
    )
    save_fig(fig, out_dir, "logistic_coefficients.png")

    return metrics
