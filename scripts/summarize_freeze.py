#!/usr/bin/env python3
"""Print key aggregates from frozen comparison_analysis.json."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _artifact_lib import MODEL_ORDER, load_comparison


def main() -> None:
    comp = load_comparison()
    pm = comp["per_model"]
    cross = comp["cross_model"]

    print("=== frozen_iterative_repair_001 summary ===")
    print(f"Shared repair slots: {cross['cases_total']}")
    print(f"Repair models: {len(MODEL_ORDER)}")
    print("Iterations: 3 (temperature 0)")
    print()
    print("Effective repair (of 45 slots):")
    for key in MODEL_ORDER:
        n = pm[key]["cases_effective_repair_at_any_iteration"]
        print(f"  {key}: {n}")
    print()
    print("Complete repair (BPR = 1.0):")
    for key in MODEL_ORDER:
        n = pm[key]["cases_complete_repair_at_any_iteration"]
        print(f"  {key}: {n}")
    print()
    print("Cross-model:")
    print(f"  improved by >=1 model: {cross['cases_improved_by_at_least_one_model']}/45")
    print(f"  improved by none:      {cross['cases_where_no_model_improved']}/45")
    print(f"  improved by all:       {cross['cases_improved_by_all_models']}/45")
    print(f"  improved by exactly 1: {cross['cases_improved_only_by_one_model']}/45")


if __name__ == "__main__":
    main()
