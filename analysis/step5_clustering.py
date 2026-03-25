"""
Step 5 — Unsupervised clustering, then comparison of cluster-based
         classification accuracy against RIPoSt-SV (~83% reference).

Approach:
  1. K-means clustering (k selected via silhouette score, k=2..6).
  2. Each cluster is assigned the majority CSED label of its members.
  3. Cluster-based classification performance is computed and compared
     to the RIPoSt-SV paper reference (83% accuracy).
  4. Cluster profiles are visualized as a heatmap (scale totals only).

Outputs:
  - Silhouette score plot (k selection).
  - Cluster profile heatmap (scale totals, standardized).
  - CSED rate bar chart per cluster.
  - CSV with cluster assignments and performance metrics.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    silhouette_score, accuracy_score,
    confusion_matrix, classification_report,
)

from .config import OUTCOME_SV, SCALE_TOTALS, ALPHA
from .utils import ensure_output_dir, save_fig, check_readability, sample_label

STEP = "step5_clustering"
RIPOST_SV_REFERENCE_ACC = 0.833  # from the paper (testing set)


def _select_k(X_scaled: np.ndarray, k_range: range) -> tuple[int, list[float]]:
    """Select best k via silhouette score."""
    scores = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        scores.append(silhouette_score(X_scaled, labels))
    best_k = k_range[int(np.argmax(scores))]
    return best_k, scores


def _plot_silhouette(k_range, scores, best_k, sample, out_dir) -> None:
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(list(k_range), scores, "o-", color="#2166ac")
    ax.axvline(best_k, color="#d6604d", linestyle="--", label=f"Best k={best_k}")
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Silhouette score")
    ax.set_title(f"K selection — {sample_label(sample)}", fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_fig(fig, out_dir, "silhouette_scores.png")


def _plot_cluster_profiles(
    profile_df: pd.DataFrame, sample: str, out_dir
) -> None:
    """Heatmap of standardized mean feature values per cluster."""
    n_vars = profile_df.shape[1]
    check_readability(n_vars, f"Cluster profiles [{sample_label(sample)}]")

    figsize = (max(8, n_vars * 0.4), max(3, profile_df.shape[0] * 0.8))
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        profile_df,
        cmap="RdBu_r", center=0,
        annot=True, fmt=".2f", annot_kws={"size": 8},
        linewidths=0.5, ax=ax,
        cbar_kws={"label": "Standardized mean"},
    )
    ax.set_title(
        f"Cluster profiles (scale totals, standardized)\n{sample_label(sample)}",
        fontweight="bold", pad=10,
    )
    ax.set_xlabel("")
    ax.set_ylabel("Cluster")
    fig.tight_layout()
    save_fig(fig, out_dir, "cluster_profiles.png")


def _plot_csed_rates(
    cluster_labels: np.ndarray, outcome: pd.Series, best_k: int, sample: str, out_dir
) -> None:
    """Bar chart: CSED+ rate per cluster."""
    df_tmp = pd.DataFrame({"cluster": cluster_labels, "csed": outcome.values})
    rates = df_tmp.groupby("cluster")["csed"].agg(["mean", "count"])
    rates.columns = ["csed_rate", "n"]

    fig, ax = plt.subplots(figsize=(max(4, best_k * 1.2), 4))
    bars = ax.bar(
        [f"Cluster {i}" for i in rates.index],
        rates["csed_rate"],
        color=["#2166ac" if r >= 0.5 else "#d6604d" for r in rates["csed_rate"]],
        edgecolor="white",
    )
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, label="50%")
    ax.set_ylim(0, 1)
    ax.set_ylabel("CSED+ rate")
    ax.set_title(
        f"Proportion CSED+ per cluster\n{sample_label(sample)}",
        fontweight="bold",
    )
    for bar, (_, row) in zip(bars, rates.iterrows()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{row['csed_rate']:.0%}\n(n={int(row['n'])})",
            ha="center", va="bottom", fontsize=9,
        )
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_fig(fig, out_dir, "csed_rate_per_cluster.png")


def run(df: pd.DataFrame, predictors: list[str], sample: str) -> dict:
    """
    Run Step 5 for a given sample dataframe.
    Returns dict with clustering performance metrics.
    """
    print(f"\n── Step 5: Clustering + comparison vs RIPoSt-SV [{sample_label(sample)}]")

    out_dir = ensure_output_dir(sample, STEP)

    # Use only scale totals for clustering (avoids collinearity, keeps it interpretable)
    cluster_features = [c for c in SCALE_TOTALS if c in df.columns]
    if len(cluster_features) < 3:
        print("  SKIP: too few scale total columns available.")
        return {}

    # Require both outcome and features; drop rows missing >50% of features
    data = df[cluster_features + [OUTCOME_SV]].copy()
    data = data.dropna(subset=[OUTCOME_SV])
    # Drop rows missing more than half the clustering features
    min_features = len(cluster_features) // 2
    data = data.dropna(thresh=min_features + 1)

    # Fill remaining feature NaNs with column median
    X_raw = data[cluster_features].apply(lambda col: col.fillna(col.median()))
    y = data[OUTCOME_SV].astype(int).reset_index(drop=True)

    n_samples = len(X_raw)
    print(f"  N={n_samples}  features={len(cluster_features)}")

    if n_samples < 20:
        print("  SKIP: fewer than 20 complete cases.")
        return {}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # Select best k
    k_range = range(2, min(7, n_samples // 10 + 2))
    best_k, sil_scores = _select_k(X_scaled, k_range)
    print(f"  Best k={best_k}  (silhouette={max(sil_scores):.3f})")
    _plot_silhouette(k_range, sil_scores, best_k, sample, out_dir)

    # Final clustering
    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = km.fit_predict(X_scaled)

    # Assign majority CSED label per cluster
    cluster_csed = {}
    for k in range(best_k):
        mask = cluster_labels == k
        majority = int(y[mask].mode()[0])
        rate = y[mask].mean()
        cluster_csed[k] = {"majority": majority, "csed_rate": rate, "n": mask.sum()}

    pred_labels = np.array([cluster_csed[k]["majority"] for k in cluster_labels])

    acc = accuracy_score(y, pred_labels)
    cm = confusion_matrix(y, pred_labels)
    report = classification_report(y, pred_labels, target_names=["CSED−", "CSED+"], zero_division=0)

    print(f"\n  Cluster-based classification accuracy: {acc:.3f}")
    print(f"  RIPoSt-SV reference accuracy (paper):  {RIPOST_SV_REFERENCE_ACC:.3f}")
    delta = acc - RIPOST_SV_REFERENCE_ACC
    direction = "higher" if delta > 0 else "lower"
    print(f"  Difference: {delta:+.3f} ({direction} than RIPoSt-SV)")
    print(f"\n  Classification report:\n{report}")

    metrics = {
        "best_k": best_k,
        "silhouette": max(sil_scores),
        "cluster_accuracy": acc,
        "ripost_sv_reference": RIPOST_SV_REFERENCE_ACC,
        "delta_vs_reference": delta,
        "n": n_samples,
    }

    # Cluster profiles (standardized means)
    profile = (
        pd.DataFrame(X_scaled, columns=cluster_features)
        .assign(cluster=cluster_labels)
        .groupby("cluster")
        .mean()
    )
    _plot_cluster_profiles(profile, sample, out_dir)
    _plot_csed_rates(cluster_labels, y, best_k, sample, out_dir)

    # Save outputs
    data_out = data.copy()
    data_out["cluster"] = cluster_labels
    data_out["cluster_pred_csed"] = pred_labels
    data_out.to_csv(out_dir / "cluster_assignments.csv", index=False)
    pd.DataFrame([metrics]).to_csv(out_dir / "clustering_metrics.csv", index=False)
    pd.DataFrame(cm, index=["True CSED−", "True CSED+"],
                 columns=["Pred CSED−", "Pred CSED+"]).to_csv(out_dir / "confusion_matrix.csv")

    return metrics
