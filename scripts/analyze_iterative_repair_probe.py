#!/usr/bin/env python3
"""Analyze iterative repair probe output from per-case artefacts (read-only)."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from repair_probe_lib import load_json, repair_repo_root, write_json

BPR_EPS = 1e-9
MAX_RAW_EXAMPLES = 3

NORMALIZED_FAILURE_CLASSES = (
    "empty_patch",
    "duplicate_transition",
    "missing_transition_to_remove",
    "self_loop_rejected",
    "missing_state",
    "update_no_change",
    "invalid_patch_schema",
    "invalid_json",
    "schema_invalid",
    "runner_failure",
    "scoring_failure",
    "abstention",
    "other_patch_application_failure",
    "other",
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe-dir", type=Path, required=True)
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="analysis.json (default: probe-dir/analysis.json)",
    )
    p.add_argument(
        "--cases-csv",
        type=Path,
        default=None,
        help="analysis_cases.csv (default: probe-dir/analysis_cases.csv)",
    )
    return p.parse_args()


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _manifest_index(probe_dir: Path) -> dict[str, dict[str, Any]]:
    path = probe_dir / "manifest.json"
    if not path.is_file():
        return {}
    data = load_json(path)
    return {e["case_id"]: e for e in data.get("entries", []) if "case_id" in e}


def _bpr_from_score(path: Path) -> float | None:
    if not path.is_file():
        return None
    data = load_json(path)
    if "error" in data and data.get("bpr") is None:
        return None
    bpr = data.get("bpr")
    return float(bpr) if bpr is not None else None


def _truncate_raw(msg: str, limit: int = 500) -> str:
    msg = msg.replace("\n", " ").strip()
    if len(msg) <= limit:
        return msg
    return msg[: limit - 3] + "..."


def _classify_patch_engine_message(text: str) -> str | None:
    """Classify apply_patch / patch-engine stderr or error line (rules 1–7)."""
    low = text.lower()
    if "[] should be non-empty" in low:
        return "empty_patch"
    if "duplicate (from, event)" in low:
        return "duplicate_transition"
    if "no transition" in low and "available:" in low:
        return "missing_transition_to_remove"
    if "self-loop" in low and "is rejected" in low:
        return "self_loop_rejected"
    if "not in states" in low:
        return "missing_state"
    if "old_to and new_to must differ" in low:
        return "update_no_change"
    if "patch schema validation failed" in low:
        return "invalid_patch_schema"
    return None


def normalize_failure_message(
    message: str | None,
    *,
    stderr: str | None = None,
) -> tuple[str, str]:
    """
    Return (normalized_class, raw_message_for_examples).
    Applies rules 1–10 in order.
    """
    raw = _truncate_raw(message or "")
    combined = raw
    if stderr:
        combined = f"{raw} | stderr: {_truncate_raw(stderr, 300)}"

    if not raw and not stderr:
        return "other", raw

    # Rule 8: subprocess wrapper — resolve underlying patch-engine message first
    low = raw.lower()
    if "returned non-zero exit status" in low or "patch_apply_or_runner" in low:
        for source in (stderr, raw):
            if not source:
                continue
            engine = _classify_patch_engine_message(source)
            if engine:
                return engine, combined
        return "other_patch_application_failure", combined

    # Rules 1–7 on primary message and stderr
    for source in (raw, stderr or ""):
        if not source:
            continue
        engine = _classify_patch_engine_message(source)
        if engine:
            return engine, combined

    if "abstention" in low or raw.endswith("abstention.json"):
        return "abstention", combined

    if "patch_generation:" in low or "patch generation" in low:
        if "invalid json" in low or "jsondecode" in low or "no json object" in low:
            return "invalid_json", combined
        return "runner_failure", combined

    if "invalid json" in low or "jsondecode" in low or "no json object" in low:
        return "invalid_json", combined

    if "schema validation" in low or "schema_invalid" in low:
        return "schema_invalid", combined

    if "scoring" in low or "score report" in low:
        return "scoring_failure", combined

    if "patch_apply" in low or "apply_patch" in low:
        return "other_patch_application_failure", combined

    return "other", combined


def _capture_apply_patch_stderr(fsm_path: Path, patch_path: Path) -> str | None:
    """Re-run apply_patch to capture stderr (does not modify probe artefacts)."""
    if not fsm_path.is_file() or not patch_path.is_file():
        return None
    repair_root = repair_repo_root()
    script = repair_root / "scripts" / "apply_patch.py"
    if not script.is_file():
        return None
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                "--fsm",
                str(fsm_path),
                "--patch",
                str(patch_path),
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
            cwd=str(repair_root),
        )
        if proc.returncode == 0:
            return None
        return (proc.stderr or proc.stdout or "").strip() or None
    finally:
        out.unlink(missing_ok=True)


def _iter_records_from_case(case_dir: Path, case_summary: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    initial_bpr = case_summary.get("initial_bpr")
    if initial_bpr is None:
        initial_bpr = _bpr_from_score(case_dir / "score_iter_00.json")

    for it in case_summary.get("iterations", []):
        idx = int(it.get("iteration", 0))
        tag = f"{idx:02d}"
        rec = dict(it)
        rec["iteration"] = idx
        score_bpr = _bpr_from_score(case_dir / f"score_iter_{tag}.json")
        if score_bpr is not None:
            rec["bpr_after"] = score_bpr
        if rec.get("bpr_before") is None and idx == 1 and initial_bpr is not None:
            rec["bpr_before"] = initial_bpr
        records.append(rec)
    return records


def _resolve_failure_for_record(
    case_dir: Path,
    rec: dict[str, Any],
) -> tuple[str, str] | None:
    """Return (normalized_class, raw_example) if this iteration has a failure event."""
    idx = rec["iteration"]
    tag = f"{idx:02d}"
    work = case_dir / f"_work_iter_{tag}"

    if rec.get("abstention") or (work / "abstention.json").is_file():
        return normalize_failure_message("abstention")

    raw_fc = str(rec.get("failure_class") or "")
    stderr: str | None = None

    if rec.get("patch_application_failure") or (
        "patch_apply_or_runner" in raw_fc and "returned non-zero exit status" in raw_fc
    ):
        patch = case_dir / f"repair_patch_iter_{tag}.json"
        if not patch.is_file():
            patch = work / "patch.json"
        if idx > 1:
            fsm_in = case_dir / f"repaired_fsm_iter_{idx - 1:02d}.json"
        else:
            fsm_in = case_dir / "candidate_initial.json"
        if not fsm_in.is_file():
            fsm_in = case_dir / "candidate_initial.json"
        stderr = _capture_apply_patch_stderr(fsm_in, patch)
        return normalize_failure_message(raw_fc or "patch_application_failure", stderr=stderr)

    if rec.get("runner_failure"):
        return normalize_failure_message(raw_fc or "runner_failure")

    if raw_fc:
        return normalize_failure_message(raw_fc)

    return None


def _collect_failure_events(
    case_dir: Path,
    records: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    events: list[tuple[str, str]] = []
    for rec in records:
        resolved = _resolve_failure_for_record(case_dir, rec)
        if resolved:
            events.append(resolved)
    return events


def _bpr_at_iteration(parsed: dict[str, Any], it: int) -> float | None:
    if it == 0:
        return parsed.get("initial_bpr")
    for rec in parsed["records"]:
        if rec["iteration"] == it:
            return rec.get("bpr_after")
    return None


def _parse_case(case_dir: Path, manifest_entry: dict[str, Any] | None) -> dict[str, Any]:
    case_id = case_dir.name
    case_summary = load_json(case_dir / "case_summary.json")
    records = _iter_records_from_case(case_dir, case_summary)

    meta = manifest_entry or {}
    system_id = meta.get("system_id") or _infer_system_id(case_id)
    source_campaign = meta.get("campaign_id") or _infer_campaign(case_id)

    initial_bpr_f = case_summary.get("initial_bpr")
    if initial_bpr_f is None:
        initial_bpr_f = _bpr_from_score(case_dir / "score_iter_00.json")
    initial_bpr_f = float(initial_bpr_f) if initial_bpr_f is not None else None

    final_bpr = None
    for rec in reversed(records):
        if rec.get("bpr_after") is not None:
            final_bpr = float(rec["bpr_after"])
            break
    if final_bpr is None:
        final_bpr = initial_bpr_f

    scored = [initial_bpr_f] if initial_bpr_f is not None else []
    scored.extend(float(r["bpr_after"]) for r in records if r.get("bpr_after") is not None)
    best_bpr = max(scored) if scored else None

    best_iteration = 0
    first_improvement: int | None = None
    if best_bpr is not None and initial_bpr_f is not None and best_bpr > initial_bpr_f + BPR_EPS:
        for rec in records:
            if rec.get("bpr_after") is not None and float(rec["bpr_after"]) >= best_bpr - BPR_EPS:
                best_iteration = rec["iteration"]
                break
        for rec in records:
            if (rec.get("delta_bpr") or 0) > BPR_EPS:
                first_improvement = rec["iteration"]
                break

    delta_best = (
        (best_bpr - initial_bpr_f)
        if best_bpr is not None and initial_bpr_f is not None
        else None
    )

    failure_events = _collect_failure_events(case_dir, records)
    dom = Counter(c for c, _ in failure_events).most_common(1)[0][0] if failure_events else ""

    return {
        "case_id": case_id,
        "system_id": system_id,
        "source_campaign": source_campaign,
        "initial_bpr": initial_bpr_f,
        "bpr_iter_1": _bpr_at_iteration({"initial_bpr": initial_bpr_f, "records": records}, 1),
        "bpr_iter_2": _bpr_at_iteration({"initial_bpr": initial_bpr_f, "records": records}, 2),
        "bpr_iter_3": _bpr_at_iteration({"initial_bpr": initial_bpr_f, "records": records}, 3),
        "final_bpr": final_bpr,
        "best_bpr": best_bpr,
        "best_iteration": best_iteration,
        "delta_best_vs_initial": delta_best,
        "improved_any": any((r.get("delta_bpr") or 0) > BPR_EPS for r in records),
        "regressed_any": any(r.get("regression") for r in records),
        "complete_repair_any": any(r.get("complete_repair") for r in records),
        "effective_repair_any": any(r.get("effective_repair") for r in records),
        "first_improvement_iteration": first_improvement,
        "iterations_attempted": len(records),
        "iterations_scored": len(scored),
        "dominant_failure_class": dom,
        "records": records,
        "failure_events": failure_events,
    }


def _infer_system_id(case_id: str) -> str:
    m = re.search(r"behavioral__([a-z0-9_]+)__qwen", case_id)
    return m.group(1) if m else ""


def _infer_campaign(case_id: str) -> str:
    if case_id.startswith("repair__c1_"):
        return "c1_pilot_ollama_behavioral"
    if case_id.startswith("repair__c2_"):
        return "c2_core_ollama_behavioral"
    return ""


def load_cases(probe_dir: Path) -> list[dict[str, Any]]:
    cases_root = probe_dir / "cases"
    if not cases_root.is_dir():
        raise FileNotFoundError(f"missing cases directory: {cases_root}")
    manifest = _manifest_index(probe_dir)
    return [_parse_case(d, manifest.get(d.name)) for d in sorted(cases_root.iterdir()) if d.is_dir()]


def _build_raw_examples(
    all_events: list[tuple[str, str]],
) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for norm, raw in all_events:
        if len(buckets[norm]) < MAX_RAW_EXAMPLES:
            if raw not in buckets[norm]:
                buckets[norm].append(raw)
    return {k: buckets[k] for k in NORMALIZED_FAILURE_CLASSES if buckets.get(k)}


def analyze(probe_dir: Path, parsed: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    probe_dir = probe_dir.resolve()
    if parsed is None:
        parsed = load_cases(probe_dir)

    run_cfg = (
        load_json(probe_dir / "run_config.json")
        if (probe_dir / "run_config.json").is_file()
        else {}
    )
    max_iter = int(run_cfg.get("max_iterations", 3) or 3)

    all_failure_events: list[tuple[str, str]] = []
    for p in parsed:
        all_failure_events.extend(p["failure_events"])

    taxonomy = Counter(norm for norm, _ in all_failure_events)
    taxonomy_out = {c: taxonomy.get(c, 0) for c in NORMALIZED_FAILURE_CLASSES}

    first_imp_dist: Counter[str] = Counter()
    for p in parsed:
        fi = p.get("first_improvement_iteration")
        first_imp_dist[str(fi) if fi is not None else "none"] += 1

    per_iteration_summary: dict[str, dict[str, Any]] = {}
    for it in range(1, max_iter + 1):
        attempted = scored = improved_prev = improved_init = 0
        unchanged_prev = regressed_prev = complete_count = 0
        deltas_prev: list[float] = []
        deltas_init: list[float] = []

        for p in parsed:
            init = p["initial_bpr"]
            if init is None:
                continue
            rec = next((r for r in p["records"] if r["iteration"] == it), None)
            if rec is None:
                continue
            attempted += 1
            after = rec.get("bpr_after")
            if after is not None:
                scored += 1
            before = rec.get("bpr_before")
            if before is None or after is None:
                continue
            d_prev = float(after) - float(before)
            d_init = float(after) - float(init)
            deltas_prev.append(d_prev)
            deltas_init.append(d_init)
            if d_prev > BPR_EPS:
                improved_prev += 1
            elif d_prev < -BPR_EPS:
                regressed_prev += 1
            else:
                unchanged_prev += 1
            if d_init > BPR_EPS:
                improved_init += 1
            if rec.get("complete_repair"):
                complete_count += 1

        per_iteration_summary[str(it)] = {
            "attempted": attempted,
            "scored": scored,
            "improved_vs_previous": improved_prev,
            "improved_vs_initial": improved_init,
            "unchanged_vs_previous": unchanged_prev,
            "regressed_vs_previous": regressed_prev,
            "complete_repairs": complete_count,
            "mean_delta_bpr_vs_previous": _mean(deltas_prev),
            "mean_delta_bpr_vs_initial": _mean(deltas_init),
        }

    initial_bprs = [p["initial_bpr"] for p in parsed if p["initial_bpr"] is not None]
    best_bprs = [p["best_bpr"] for p in parsed if p["best_bpr"] is not None]
    final_bprs = [p["final_bpr"] for p in parsed if p["final_bpr"] is not None]

    mode = run_cfg.get("mode", "unknown")
    return {
        "probe_dir": str(probe_dir),
        "probe_id": run_cfg.get("probe_id"),
        "mode": mode,
        "dry_run": mode == "dry_run",
        "max_iterations_configured": max_iter,
        "cases_attempted": len(parsed),
        "cases_improved_at_any_iteration": sum(1 for p in parsed if p["improved_any"]),
        "cases_regressed_at_any_iteration": sum(1 for p in parsed if p["regressed_any"]),
        "cases_complete_repair_at_any_iteration": sum(1 for p in parsed if p["complete_repair_any"]),
        "cases_effective_repair_at_any_iteration": sum(1 for p in parsed if p["effective_repair_any"]),
        "mean_initial_bpr": _mean(initial_bprs),
        "mean_best_bpr": _mean(best_bprs),
        "mean_final_bpr": _mean(final_bprs),
        "first_improvement_iteration_distribution": dict(first_imp_dist),
        "per_iteration_summary": per_iteration_summary,
        "failure_taxonomy_normalized": taxonomy_out,
        "raw_failure_examples": _build_raw_examples(all_failure_events),
        "failure_events_total": len(all_failure_events),
    }


def write_cases_csv(path: Path, parsed: list[dict[str, Any]]) -> None:
    fields = [
        "case_id",
        "system_id",
        "source_campaign",
        "initial_bpr",
        "bpr_iter_1",
        "bpr_iter_2",
        "bpr_iter_3",
        "final_bpr",
        "best_bpr",
        "best_iteration",
        "delta_best_vs_initial",
        "improved_any",
        "regressed_any",
        "complete_repair_any",
        "effective_repair_any",
        "first_improvement_iteration",
        "dominant_failure_class",
        "iterations_attempted",
        "iterations_scored",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for p in parsed:
            w.writerow({k: p.get(k) for k in fields})


def _print_report(analysis: dict[str, Any], parsed: list[dict[str, Any]]) -> None:
    print("\n=== failure_taxonomy_normalized ===")
    for cls, count in analysis["failure_taxonomy_normalized"].items():
        if count:
            print(f"  {cls}: {count}")

    print("\n=== per_iteration_summary ===")
    print(json.dumps(analysis["per_iteration_summary"], indent=2))

    improved = sorted(
        [
            p
            for p in parsed
            if p.get("improved_any") and (p.get("delta_best_vs_initial") or 0) > BPR_EPS
        ],
        key=lambda p: p.get("delta_best_vs_initial") or 0,
        reverse=True,
    )
    print("\n=== top improved cases (by delta_best_vs_initial) ===")
    for p in improved[:10]:
        fi = p.get("first_improvement_iteration")
        fi_s = str(fi) if fi is not None else "none"
        print(
            f"  {p['case_id']} | {p['system_id']} | "
            f"initial={p['initial_bpr']:.4f} best={p['best_bpr']:.4f} "
            f"delta={p['delta_best_vs_initial']:.4f} first_imp@iter{fi_s}"
        )

    regressed = sorted(
        [p for p in parsed if p.get("regressed_any")],
        key=lambda p: (p.get("initial_bpr") or 0),
    )
    print("\n=== top regressed cases ===")
    for p in regressed:
        b1, b2, b3 = p.get("bpr_iter_1"), p.get("bpr_iter_2"), p.get("bpr_iter_3")
        print(
            f"  {p['case_id']} | {p['system_id']} | "
            f"initial={p['initial_bpr']:.4f} iter1={b1} iter2={b2} iter3={b3} final={p['final_bpr']:.4f}"
        )


def main() -> int:
    args = _parse_args()
    probe_dir = args.probe_dir.resolve()
    out_json = (args.output or probe_dir / "analysis.json").resolve()
    out_csv = (args.cases_csv or probe_dir / "analysis_cases.csv").resolve()

    try:
        parsed = load_cases(probe_dir)
        analysis = analyze(probe_dir, parsed)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 2

    write_json(out_json, analysis)
    write_cases_csv(out_csv, parsed)
    _print_report(analysis, parsed)

    print(f"\nWrote {out_json}")
    print(f"Wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
