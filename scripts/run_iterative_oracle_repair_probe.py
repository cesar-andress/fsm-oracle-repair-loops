#!/usr/bin/env python3
"""
Feasibility probe: iterative oracle-guided repair (max_iterations configurable).

Use --dry-run to validate inputs without calling Ollama.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repair_probe_lib import (
    REPAIR_CONDITION,
    apply_patch_paths,
    build_oracle_feedback,
    classify_iteration_outcome,
    load_json,
    repair_repo_root,
    resolve_case_paths,
    score_fsm_paths,
    validate_manifest_entry,
    write_json,
)

PROBE_ID = "iterative_repair_probe_001"


def _select_manifest_entries(
    manifest: dict[str, Any],
    *,
    limit: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate manifest rows, apply --limit after validation; build selection report."""
    all_entries = list(manifest.get("entries", []))
    manifest_entries_total = len(all_entries)
    pool_eligible = manifest.get("eligible_count")

    skipped_by_reason: dict[str, int] = {}
    skipped_cases: list[dict[str, str]] = []
    valid_entries: list[dict[str, Any]] = []

    for entry in all_entries:
        case_id = entry.get("case_id", "<unknown>")
        issues = validate_manifest_entry(entry)
        if issues:
            reason = "manifest_entry_invalid"
            skipped_by_reason[reason] = skipped_by_reason.get(reason, 0) + 1
            skipped_cases.append({"case_id": case_id, "reason": reason, "detail": "; ".join(issues)})
            continue
        valid_entries.append(entry)

    eligible_before_limit = len(valid_entries)
    selected = valid_entries if limit is None else valid_entries[:limit]
    selected_after_limit = len(selected)

    if limit is not None and eligible_before_limit > limit:
        n = eligible_before_limit - limit
        skipped_by_reason["runner_limit"] = skipped_by_reason.get("runner_limit", 0) + n
        for entry in valid_entries[limit:]:
            skipped_cases.append(
                {"case_id": entry["case_id"], "reason": "runner_limit", "detail": f"limit={limit}"}
            )

    excluded_at_manifest_build: int | None = None
    if isinstance(pool_eligible, int) and pool_eligible > manifest_entries_total:
        excluded_at_manifest_build = pool_eligible - manifest_entries_total
        skipped_by_reason["excluded_at_manifest_build"] = excluded_at_manifest_build

    skipped_in_manifest = manifest_entries_total - selected_after_limit
    skipped_total = skipped_in_manifest + (excluded_at_manifest_build or 0)
    report: dict[str, Any] = {
        "manifest_entries_total": manifest_entries_total,
        "manifest_pool_eligible_count": pool_eligible,
        "excluded_at_manifest_build": excluded_at_manifest_build,
        "eligible_before_limit": eligible_before_limit,
        "limit_requested": limit,
        "selected_after_limit": selected_after_limit,
        "skipped_total": skipped_total,
        "skipped_by_reason": skipped_by_reason,
        "selected_case_ids": [e["case_id"] for e in selected],
        "skipped_cases": skipped_cases,
        "input_manifest_probe_id": manifest.get("probe_id"),
        "model_filter": manifest.get("model_filter"),
    }
    return selected, report


def _print_selection_summary(report: dict[str, Any]) -> None:
    total = report["manifest_entries_total"]
    pool = report.get("manifest_pool_eligible_count")
    eligible = report["eligible_before_limit"]
    selected = report["selected_after_limit"]
    limit = report.get("limit_requested")
    excluded_build = report.get("excluded_at_manifest_build")

    lines = [
        f"Selection: {selected} case(s) to run "
        f"(manifest entries={total}, valid={eligible}, limit={limit!r}).",
    ]
    if pool is not None:
        lines.append(
            f"  Manifest pool: {pool} eligible at build time; "
            f"{excluded_build or 0} not included in manifest file."
        )
    reasons = report.get("skipped_by_reason") or {}
    if reasons:
        parts = [f"{k}={v}" for k, v in sorted(reasons.items())]
        lines.append(f"  Skipped: {', '.join(parts)}.")
    print("\n".join(lines), flush=True)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-manifest", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--model", default="qwen2.5-coder:7b")
    p.add_argument("--max-iterations", type=int, default=3)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--limit", type=int, default=None, help="subset of manifest entries")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--repair-repo",
        type=Path,
        default=None,
        help="fsm-repairability-study root (default: ../ist2026b/...)",
    )
    return p.parse_args()


def _run_config(args: argparse.Namespace, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_id": manifest.get("probe_id", PROBE_ID),
        "mode": "dry_run" if args.dry_run else "live",
        "model": args.model,
        "max_iterations": args.max_iterations,
        "temperature": args.temperature,
        "repair_condition": manifest.get("repair_condition", REPAIR_CONDITION),
        "repair_repo": str((args.repair_repo or repair_repo_root()).resolve()),
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _dry_run_case(
    entry: dict[str, Any],
    case_out: Path,
    *,
    max_iterations: int,
) -> dict[str, Any]:
    case_out.mkdir(parents=True, exist_ok=True)
    cand_src = Path(entry["candidate_fsm_path"])
    shutil.copy2(cand_src, case_out / "candidate_initial.json")

    bpr0 = float(entry.get("initial_bpr", 0.0))
    write_json(
        case_out / "score_iter_00.json",
        {
            "dry_run": True,
            "iteration": 0,
            "bpr": bpr0,
            "structurally_valid": entry.get("structurally_valid", True),
        },
    )

    iteration_summaries: list[dict[str, Any]] = []
    for it in range(1, max_iterations + 1):
        tag = f"{it:02d}"
        write_json(
            case_out / f"oracle_feedback_iter_{tag}.json",
            {"dry_run": True, "iteration": it, "level": "trace"},
        )
        (case_out / f"prompt_iter_{tag}.txt").write_text(
            "# dry-run placeholder prompt\n", encoding="utf-8"
        )
        (case_out / f"raw_output_iter_{tag}.txt").write_text(
            "# dry-run: no Ollama call\n", encoding="utf-8"
        )
        write_json(
            case_out / f"repair_patch_iter_{tag}.json",
            {"dry_run": True, "operations": []},
        )
        shutil.copy2(cand_src, case_out / f"repaired_fsm_iter_{tag}.json")
        write_json(
            case_out / f"score_iter_{tag}.json",
            {"dry_run": True, "iteration": it, "bpr": bpr0},
        )
        iteration_summaries.append(
            {
                "iteration": it,
                "bpr_before": bpr0,
                "bpr_after": bpr0,
                "delta_bpr": 0.0,
                "effective_repair": False,
                "complete_repair": False,
                "regression": False,
                "abstention": False,
                "patch_application_failure": False,
                "runner_failure": False,
                "failure_class": "dry_run_placeholder",
                "dry_run": True,
            }
        )

    return {
        "case_id": entry["case_id"],
        "initial_bpr": bpr0,
        "structurally_valid": entry.get("structurally_valid", True),
        "iterations": iteration_summaries,
        "dry_run": True,
    }


def _live_case(
    entry: dict[str, Any],
    case_out: Path,
    *,
    args: argparse.Namespace,
    repair_root: Path,
) -> dict[str, Any]:
    """Live Ollama path — requires Ollama and explicit user approval."""
    sys.path.insert(0, str(repair_root / "scripts"))
    from generate_patch_ollama import (  # noqa: E402
        PatchAbstention,
        PatchGenerationError,
        generate_patch_ollama,
    )
    from ollama_client import OllamaConfig  # noqa: E402

    paths = resolve_case_paths(Path(entry["case_dir"]))
    case_id = entry["case_id"]
    case_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths["candidate_fsm"], case_out / "candidate_initial.json")

    current_fsm = paths["candidate_fsm"]
    oracle = paths["oracle_suite"]
    score_path = case_out / "score_iter_00.json"
    report0 = score_fsm_paths(current_fsm, oracle, score_path, repair_root=repair_root)
    bpr = float(report0["bpr"])

    iteration_summaries: list[dict[str, Any]] = []
    run_id = f"{PROBE_ID}__{case_id}"
    condition = REPAIR_CONDITION
    patch_schema = repair_root / "schemas" / "patch.schema.json"
    ollama_cfg = OllamaConfig()

    for it in range(1, args.max_iterations + 1):
        tag = f"{it:02d}"
        bpr_before = bpr
        prev_score = case_out / f"score_iter_{it-1:02d}.json" if it > 1 else score_path
        feedback_path = case_out / f"oracle_feedback_iter_{tag}.json"
        build_oracle_feedback(
            prev_score,
            case_id=case_id,
            run_id=run_id,
            iteration_index=it,
            output_path=feedback_path,
            repair_root=repair_root,
        )

        work = case_out / f"_work_iter_{tag}"
        work.mkdir(parents=True, exist_ok=True)
        abstention = False
        patch_failure = False
        runner_failure = False
        failure_class = None
        patch_applied = False

        try:
            generate_patch_ollama(
                condition=condition,
                requirement_path=paths["requirement"],
                candidate_fsm_path=current_fsm,
                diagnostic_path=feedback_path,
                patch_schema_path=patch_schema,
                model=args.model,
                output_dir=work,
                ollama_config=ollama_cfg,
                generate_options={"temperature": args.temperature},
                prompt_variant="default",
            )
            for src, dst in (
                (work / "prompt.txt", case_out / f"prompt_iter_{tag}.txt"),
                (work / "raw_response.txt", case_out / f"raw_output_iter_{tag}.txt"),
                (work / "patch.json", case_out / f"repair_patch_iter_{tag}.json"),
            ):
                if src.is_file():
                    shutil.copy2(src, dst)
            patch_path = work / "patch.json"
            repaired = case_out / f"repaired_fsm_iter_{tag}.json"
            apply_patch_paths(current_fsm, patch_path, repaired, repair_root=repair_root)
            patch_applied = True
            current_fsm = repaired
        except PatchAbstention:
            abstention = True
            failure_class = "abstention"
        except PatchGenerationError as exc:
            runner_failure = True
            failure_class = f"patch_generation:{exc}"
        except Exception as exc:
            patch_failure = True
            failure_class = f"patch_apply_or_runner:{exc}"

        iter_score = case_out / f"score_iter_{tag}.json"
        if patch_applied:
            report = score_fsm_paths(current_fsm, oracle, iter_score, repair_root=repair_root)
            bpr = float(report["bpr"])
        else:
            write_json(iter_score, {"bpr": bpr_before, "note": "no patch applied"})
            bpr = bpr_before

        outcome = classify_iteration_outcome(
            bpr_before,
            bpr,
            patch_applied=patch_applied,
            abstention=abstention,
            patch_failure=patch_failure,
            runner_failure=runner_failure,
        )
        outcome.update(
            iteration=it,
            failure_class=failure_class,
            raw_model_output_path=str(case_out / f"raw_output_iter_{tag}.txt"),
            prompt_path=str(case_out / f"prompt_iter_{tag}.txt"),
            repaired_fsm_path=str(case_out / f"repaired_fsm_iter_{tag}.json"),
        )
        iteration_summaries.append(outcome)
        if outcome["complete_repair"]:
            break

    return {
        "case_id": case_id,
        "initial_bpr": float(report0["bpr"]),
        "structurally_valid": entry.get("structurally_valid", True),
        "iterations": iteration_summaries,
        "dry_run": False,
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = args.input_manifest.resolve()
    out_dir = args.output_dir.resolve()
    manifest = load_json(manifest_path)

    entries, selection_report = _select_manifest_entries(manifest, limit=args.limit)
    invalid = [
        s for s in selection_report.get("skipped_cases", []) if s.get("reason") == "manifest_entry_invalid"
    ]
    if invalid:
        raise SystemExit(
            "manifest validation failed:\n"
            + "\n".join(f"{s['case_id']}: {s.get('detail', '')}" for s in invalid)
        )

    _print_selection_summary(selection_report)

    out_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = out_dir / "cases"
    cases_dir.mkdir(exist_ok=True)

    repair_root = (args.repair_repo or repair_repo_root()).resolve()
    run_cfg = _run_config(args, manifest)
    write_json(out_dir / "run_config.json", run_cfg)
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "selection_report.json", selection_report)

    case_summaries: list[dict[str, Any]] = []
    for entry in entries:
        case_id = entry["case_id"]
        case_out = cases_dir / case_id
        if args.dry_run:
            summary = _dry_run_case(entry, case_out, max_iterations=args.max_iterations)
        else:
            summary = _live_case(entry, case_out, args=args, repair_root=repair_root)
        write_json(case_out / "case_summary.json", summary)
        case_summaries.append(summary)

    probe_summary = {
        "probe_id": manifest.get("probe_id", PROBE_ID),
        "mode": run_cfg["mode"],
        "cases_attempted": len(case_summaries),
        "model": args.model,
        "max_iterations": args.max_iterations,
        "temperature": args.temperature,
        "case_summaries": case_summaries,
    }
    write_json(out_dir / "summary.json", probe_summary)

    if args.dry_run:
        write_json(
            out_dir / "dry_run_summary.json",
            {
                "status": "ok",
                "cases": len(case_summaries),
                "message": "Dry run completed; no Ollama calls.",
            },
        )

    # CSV
    import csv

    csv_path = out_dir / "summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "case_id",
                "iteration",
                "bpr_before",
                "bpr_after",
                "delta_bpr",
                "effective_repair",
                "complete_repair",
                "regression",
                "abstention",
                "patch_application_failure",
                "runner_failure",
                "failure_class",
                "dry_run",
            ]
        )
        for cs in case_summaries:
            for it in cs.get("iterations", []):
                w.writerow(
                    [
                        cs["case_id"],
                        it.get("iteration"),
                        it.get("bpr_before"),
                        it.get("bpr_after"),
                        it.get("delta_bpr"),
                        it.get("effective_repair"),
                        it.get("complete_repair"),
                        it.get("regression"),
                        it.get("abstention"),
                        it.get("patch_application_failure"),
                        it.get("runner_failure"),
                        it.get("failure_class"),
                        cs.get("dry_run"),
                    ]
                )

    return probe_summary


def main() -> int:
    args = _parse_args()
    try:
        summary = run_probe(args)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "cases": summary["cases_attempted"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
