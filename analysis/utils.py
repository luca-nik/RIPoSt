"""
Shared plotting utilities, saving helpers, and readability warnings.
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from .config import OUTPUT_DIR, MAX_VARS_READABLE, ALPHA


def ensure_output_dir(sample: str, step: str) -> Path:
    """Create and return output subdirectory for a given sample and step."""
    path = OUTPUT_DIR / sample / step
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_readability(n_vars: int, plot_name: str) -> bool:
    """
    Warn if the number of variables exceeds the readable threshold.
    Returns True if readable, False if flagged.
    """
    if n_vars > MAX_VARS_READABLE:
        print(
            f"\n[READABILITY WARNING] '{plot_name}' would display {n_vars} variables "
            f"(threshold: {MAX_VARS_READABLE}). The plot may be hard to read. "
            "Consider using a grouped or filtered view.\n"
        )
        return False
    return True


def save_fig(fig: plt.Figure, path: Path, filename: str, dpi: int = 150) -> None:
    """Save a figure to disk and close it."""
    filepath = path / filename
    fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {filepath.relative_to(OUTPUT_DIR.parent)}")


def significance_stars(p: float) -> str:
    """Return significance stars for a p-value."""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < ALPHA:
        return "*"
    return ""


def make_bar_chart(
    labels: list[str],
    values: list[float],
    errors: list[float] | None,
    title: str,
    xlabel: str,
    color_values: list[float] | None = None,
    color_threshold: float = ALPHA,
    figsize: tuple | None = None,
    vline: float | None = 0.0,
) -> plt.Figure:
    """
    Horizontal bar chart sorted by absolute value of `values`.
    Bars are colored by significance (dark = significant, light = not).
    `color_values` should be a list of p-values when used for significance coloring.
    """
    # Sort by absolute value descending
    order = np.argsort(np.abs(values))[::-1]
    labels  = [labels[i] for i in order]
    values  = [values[i] for i in order]
    if errors is not None:
        errors = [errors[i] for i in order]
    if color_values is not None:
        color_values = [color_values[i] for i in order]

    n = len(labels)
    if figsize is None:
        figsize = (8, max(4, n * 0.35))

    fig, ax = plt.subplots(figsize=figsize)

    colors = []
    for i, v in enumerate(values):
        if color_values is not None:
            sig = color_values[i] < color_threshold
        else:
            sig = True
        if sig:
            colors.append("#2166ac" if v >= 0 else "#d6604d")
        else:
            colors.append("#92c5de" if v >= 0 else "#f4a582")

    y_pos = np.arange(n)
    ax.barh(
        y_pos, values,
        xerr=errors,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
        capsize=3,
        error_kw={"elinewidth": 0.8},
    )

    if vline is not None:
        ax.axvline(vline, color="black", linewidth=0.8, linestyle="--")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)

    # Legend for significance
    if color_values is not None:
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#2166ac", label="Significant positive"),
            Patch(facecolor="#d6604d", label="Significant negative"),
            Patch(facecolor="#92c5de", label="Non-significant positive"),
            Patch(facecolor="#f4a582", label="Non-significant negative"),
        ]
        ax.legend(handles=legend_elements, fontsize=7, loc="lower right")

    fig.tight_layout()
    return fig


def sample_label(sample: str) -> str:
    """Human-readable label for a sample."""
    return {
        "full": "Full sample (n=200)",
        "inat": "INAT subtype",
        "comb": "COMB subtype",
        "iper": "IPER subtype (n=4, descriptive only)",
    }.get(sample, sample)
