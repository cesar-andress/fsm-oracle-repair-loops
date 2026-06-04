#!/usr/bin/env python3
"""Compare iterative repair probe runs across repair models (read-only)."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from repair_probe_lib import load_json, write_json

BPR_EPS = 1e-9


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--runs",
        nargs="+",
        required=True,
        metavar="MODEL=DIR",
        help="e.g. qwen=../paper/experiments/iterative_repair_probe_002_live_025",
    )
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def _parse_runs(specs: list[str]) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for spec in specs:
        if "=" not in spec:
            raise SystemExit(f"invalid --runs entry (expected MODEL=DIR): {spec}")
        name, path = spec.split("=", 1)
        name = name.strip()
        if not name:
            raise SystemExit(f"empty model name in: {spec}")
        out[name] = Path(path).resolve()
    return out


def _load_analysis(probe_dir: Path) -> dict[str, Any]:
    path = probe_dir / "analysis.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing analysis.json in {probe_dir} (run analyze_iterative_repair_probe.py first)")
    return load_json(path)


def _load_cases_csv(probe_dir: Path) -> list[dict[str, str]]:
    path = probe_dir / "analysis_cases.csv"
    if not path.is_file():
        raise FileNotFoundError(f"missing analysis_cases.csv in {probe_dir}")
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _bool_cell(value: str | None) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def _float_cell(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _model_summary(analysis: dict[str, Any], probe_dir: Path) -> dict[str, Any]:
    cases = _load_cases_csv(probe_dir)
    deltas = [
        _float_cell(r.get("delta_best_vs_initial"))
        for r in cases
        if _float_cell(r.get("delta_best_vs_initial")) is not None
    ]
    return {
        "probe_dir": str(probe_dir),
        "repair_model": load_json(probe_dir / "run_config.json").get("model") if (probe_dir / "run_config.json").is_file() else None,
        "cases_attempted": analysis.get("cases_attempted"),
        "cases_improved_at_any_iteration": analysis.get("cases_improved_at_any_iteration"),
        "cases_regressed_at_any_iteration": analysis.get("cases_regressed_at_any_iteration"),
        "cases_complete_repair_at_any_iteration": analysis.get("cases_complete_repair_at_any_iteration"),
        "cases_effective_repair_at_any_iteration": analysis.get("cases_effective_repair_at_any_iteration"),
        "mean_initial_bpr": analysis.get("mean_initial_bpr"),
        "mean_best_bpr": analysis.get("mean_best_bpr"),
        "mean_final_bpr": analysis.get("mean_final_bpr"),
        "mean_delta_best_vs_initial": analysis.get("mean_delta_best_vs_initial")
        if analysis.get("mean_delta_best_vs_initial") is not None
        else (statistics.fmean(deltas) if deltas else None),
        "first_improvement_iteration_distribution": analysis.get("first_improvement_iteration_distribution"),
        "failure_taxonomy_normalized": analysis.get("failure_taxonomy_normalized"),
        "failure_events_total": analysis.get("failure_events_total"),
    }


def _cross_model(case_tables: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    models = sorted(case_tables.keys())
    by_case: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for model, rows in case_tables.items():
        for row in rows:
            cid = row["case_id"]
            by_case[cid][model] = {
                "improved_any": _bool_cell(row.get("improved_any")),
                "delta_best_vs_initial": _float_cell(row.get("delta_best_vs_initial")) or 0.0,
                "dominant_failure_class": (row.get("dominant_failure_class") or "").strip() or None,
                "best_bpr": _float_cell(row.get("best_bpr")),
            }

    all_cases = sorted(by_case.keys())
    improved_by_any: list[str] = []
    improved_by_all: list[str] = []
    improved_only_one: list[str] = []
    no_improvement: list[str] = []
    best_model_per_case: dict[str, str | None] = {}

    for cid in all_cases:
        per = by_case[cid]
        improved_models = [m for m in models if per.get(m, {}).get("improved_any")]
        if improved_models:
            improved_by_any.append(cid)
        else:
            no_improvement.append(cid)
        if len(improved_models) == len(models) and models:
            improved_by_all.append(cid)
        if len(improved_models) == 1:
            improved_only_one.append({"case_id": cid, "model": improved_models[0]})

        best_m = None
        best_d = -1.0
        for m in models:
            d = per.get(m, {}).get("delta_best_vs_initial", 0.0) or 0.0
            if d > best_d + BPR_EPS:
                best_d = d
                best_m = m
            elif abs(d - best_d) <= BPR_EPS and d > BPR_EPS:
                best_m = f"{best_m},{m}" if best_m else m
        best_model_per_case[cid] = best_m

    failure_classes_by_model: dict[str, set[str]] = {}
    for model, rows in case_tables.items():
        failure_classes_by_model[model] = {
            (r.get("dominant_failure_class") or "").strip()
            for r in rows
            if (r.get("dominant_failure_class") or "").strip()
        }

    all_failure_classes: set[str] = set()
    for s in failure_classes_by_model.values():
        all_failure_classes |= s
    overlap_all_models = (
        set.intersection(*failure_classes_by_model.values())
        if failure_classes_by_model
        else set()
    )
    pairwise_overlap: dict[str, int] = {}
    for i, m1 in enumerate(models):
        for m2 in models[i + 1 :]:
            pairwise_overlap[f"{m1}|{m2}"] = len(
                failure_classes_by_model[m1] & failure_classes_by_model[m2]
            )

    per_case_failure_sets: dict[str, dict[str, str | None]] = {
        cid: {m: by_case[cid].get(m, {}).get("dominant_failure_class") for m in models}
        for cid in all_cases
    }
    same_dominant_all = [
        cid
        for cid, fm in per_case_failure_sets.items()
        if len({v for v in fm.values() if v}) == 1 and any(fm.values())
    ]

    return {
        "models": models,
        "cases_total": len(all_cases),
        "cases_improved_by_at_least_one_model": len(improved_by_any),
        "cases_improved_by_all_models": len(improved_by_all),
        "cases_improved_only_by_one_model": len(improved_only_one),
        "cases_improved_only_by_one_model_detail": improved_only_one,
        "cases_where_no_model_improved": len(no_improvement),
        "cases_where_no_model_improved_ids": no_improvement,
        "best_model_per_case": best_model_per_case,
        "dominant_failure_class_overlap_all_models": sorted(overlap_all_models),
        "dominant_failure_pairwise_overlap_counts": pairwise_overlap,
        "cases_same_dominant_failure_all_models": len(same_dominant_all),
        "failure_taxonomy_union_counts": dict(
            Counter(
                cls
                for rows in case_tables.values()
                for r in rows
                for cls in [(r.get("dominant_failure_class") or "").strip()]
                if cls
            )
        ),
    }


def _write_failure_taxonomy_csv(path: Path, summaries: dict[str, dict[str, Any]]) -> None:
    rows: list[dict[str, Any]] = []
    all_classes: set[str] = set()
    for summary in summaries.values():
        tax = summary.get("failure_taxonomy_normalized") or {}
        all_classes |= {k for k, v in tax.items() if v}
    for model, summary in sorted(summaries.items()):
        tax = summary.get("failure_taxonomy_normalized") or {}
        for cls in sorted(all_classes):
            rows.append(
                {
                    "model": model,
                    "failure_class": cls,
                    "count": tax.get(cls, 0),
                    "failure_events_total": summary.get("failure_events_total"),
                }
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["model", "failure_class", "count", "failure_events_total"])
        w.writeheader()
        w.writerows(rows)


def _write_model_summary_csv(path: Path, summaries: dict[str, dict[str, Any]]) -> None:
    fields = [
        "model",
        "probe_dir",
        "repair_model",
        "cases_attempted",
        "cases_improved_at_any_iteration",
        "cases_regressed_at_any_iteration",
        "cases_complete_repair_at_any_iteration",
        "cases_effective_repair_at_any_iteration",
        "mean_initial_bpr",
        "mean_best_bpr",
        "mean_final_bpr",
        "mean_delta_best_vs_initial",
        "failure_events_total",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for model, s in sorted(summaries.items()):
            row = {"model": model}
            for k in fields:
                if k != "model":
                    row[k] = s.get(k)
            w.writerow(row)


def _write_cases_csv(
    path: Path,
    models: list[str],
    case_tables: dict[str, list[dict[str, str]]],
    cross: dict[str, Any],
) -> None:
    index: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    meta: dict[str, dict[str, str]] = {}
    for model, rows in case_tables.items():
        for row in rows:
            cid = row["case_id"]
            index[cid][model] = row
            if cid not in meta:
                meta[cid] = {
                    "case_id": cid,
                    "system_id": row.get("system_id", ""),
                    "source_campaign": row.get("source_campaign", ""),
                    "initial_bpr": row.get("initial_bpr", ""),
                }

    fields = ["case_id", "system_id", "source_campaign", "initial_bpr", "best_model"]
    for m in models:
        fields.extend(
            [
                f"{m}_improved_any",
                f"{m}_delta_best_vs_initial",
                f"{m}_best_bpr",
                f"{m}_dominant_failure_class",
            ]
        )
    fields.append("any_model_improved")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for cid in sorted(index.keys()):
            row = dict(meta[cid])
            row["best_model"] = cross["best_model_per_case"].get(cid)
            any_imp = False
            for m in models:
                r = index[cid].get(m, {})
                imp = _bool_cell(r.get("improved_any"))
                row[f"{m}_improved_any"] = imp
                row[f"{m}_delta_best_vs_initial"] = r.get("delta_best_vs_initial", "")
                row[f"{m}_best_bpr"] = r.get("best_bpr", "")
                row[f"{m}_dominant_failure_class"] = r.get("dominant_failure_class", "")
                any_imp = any_imp or imp
            row["any_model_improved"] = any_imp
            w.writerow(row)


def main() -> int:
    args = _parse_args()
    run_dirs = _parse_runs(args.runs)
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    analyses: dict[str, dict[str, Any]] = {}
    summaries: dict[str, dict[str, Any]] = {}
    case_tables: dict[str, list[dict[str, str]]] = {}

    for model, probe_dir in run_dirs.items():
        if not probe_dir.is_dir():
            print(f"error: probe dir not found for {model}: {probe_dir}", file=sys.stderr)
            return 2
        analyses[model] = _load_analysis(probe_dir)
        summaries[model] = _model_summary(analyses[model], probe_dir)
        case_tables[model] = _load_cases_csv(probe_dir)

    cross = _cross_model(case_tables)
    comparison = {
        "output_dir": str(out_dir),
        "runs": {m: str(p) for m, p in run_dirs.items()},
        "per_model": summaries,
        "cross_model": cross,
    }

    write_json(out_dir / "comparison_analysis.json", comparison)
    _write_model_summary_csv(out_dir / "comparison_model_summary.csv", summaries)
    _write_failure_taxonomy_csv(out_dir / "comparison_failure_taxonomy.csv", summaries)
    _write_cases_csv(out_dir / "comparison_cases.csv", cross["models"], case_tables, cross)

    print(json.dumps({"status": "ok", "output_dir": str(out_dir), "models": cross["models"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
