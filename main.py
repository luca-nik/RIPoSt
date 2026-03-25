#!/usr/bin/env python3
"""
RIPoSt Analysis — main entry point.

Usage examples:
  uv run python main.py                          # full analysis, all samples
  uv run python main.py --steps 1 2             # only Spearman + LASSO-NED, all samples
  uv run python main.py --samples inat comb     # all steps, INAT and COMB only
  uv run python main.py --steps 3 --samples full comb
"""
import argparse
import sys
import warnings
from pathlib import Path

# Suppress sklearn FutureWarnings from transitional API changes
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from analysis.data import prepare
from analysis import (
    step1_spearman,
    step2_lasso_ned,
    step3_association,
    step4_logistic,
    step5_clustering,
)
from analysis.config import OUTPUT_DIR

STEPS = {
    "1": ("Spearman correlation → RIPoSt-NED",        step1_spearman),
    "2": ("LASSO linear regression → RIPoSt-NED",     step2_lasso_ned),
    "3": ("Association analysis → RIPoSt-SV",          step3_association),
    "4": ("LASSO logistic regression → RIPoSt-SV",    step4_logistic),
    "5": ("Clustering + RIPoSt-SV comparison",         step5_clustering),
}

SAMPLES = ["full", "inat", "comb"]  # 'iper' excluded from inferential analyses


def parse_args():
    parser = argparse.ArgumentParser(
        description="RIPoSt correlation and classification analysis.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--steps", nargs="+", default=list(STEPS.keys()),
        choices=list(STEPS.keys()),
        metavar="STEP",
        help=(
            "Steps to run (default: all).\n"
            + "\n".join(f"  {k}: {v[0]}" for k, v in STEPS.items())
        ),
    )
    parser.add_argument(
        "--samples", nargs="+", default=SAMPLES,
        choices=["full", "inat", "comb"],
        metavar="SAMPLE",
        help="Samples to analyse: full | inat | comb  (default: all three)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  RIPoSt Analysis")
    print(f"  Steps:   {', '.join(args.steps)}")
    print(f"  Samples: {', '.join(args.samples)}")
    print(f"  Output:  {OUTPUT_DIR}")
    print("=" * 60)

    for sample in args.samples:
        print(f"\n{'━' * 60}")
        print(f"  SAMPLE: {sample.upper()}")
        print(f"{'━' * 60}")

        df, predictors = prepare(sample)
        print(f"  Loaded {len(df)} patients, {len(predictors)} predictors.")

        for step_key in args.steps:
            _, module = STEPS[step_key]
            module.run(df, predictors, sample)

    print(f"\n{'=' * 60}")
    print(f"  Done. All outputs saved to: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
