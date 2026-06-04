#!/usr/bin/env python3
"""
Build feasibility manifest and inventory from pilot repair cases (EMSE/IST lineage).

Does not run Ollama or modify prior experiments.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from repair_probe_lib import (
    DEFAULT_CASES_ROOT,
    DEFAULT_SELECTION_CSV,
    check_structural_validity,
    load_json,
    repair_repo_root,
    score_fsm_paths,
    write_json,
)

PROBE_ID = "iterative_repair_probe_001"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--cases-root",
        type=Path,
        default=DEFAULT_CASES_ROOT,
        help="pilot_repair_cases_diverse directory",
    )
    p.add_argument(
        "--selection-csv",
        type=Path,
        default=None,
        help="candidate_selection_report.csv (default: under cases-root)",
    )
    p.add_argument(
        "--output-manifest",
        type=Path,
        required=True,
        help="manifest.json path to write",
    )
    p.add_argument(
        "--inventory-report",
        type=Path,
        default=None,
        help="optional markdown inventory report",
    )
    p.add_argument(
        "--model",
        default="qwen2.5-coder:7b",
        help="Ollama model tag for live probe; manifest filter accepts :7b or _7b ids",
    )
    p.add_argument("--limit", type=int, default=15, help="max cases in manifest")
    p.add_argument(
        "--reverify-bpr",
        action="store_true",
        help="re-score candidate FSMs (slower, deterministic)",
    )
    return p.parse_args()


def _model_matches(row: dict[str, str], model_filter: str) -> bool:
    """Match CSV model_id (often qwen2.5-coder_7b) to Ollama tag (qwen2.5-coder:7b)."""
    mid = row.get("model_id") or ""
    if model_filter in mid or mid in model_filter:
        return True
    normalized = model_filter.replace(":", "_").replace(".", "_")
    mid_norm = mid.replace(":", "_").replace(".", "_")
    return normalized in mid_norm or "qwen2_5_coder_7b" in row.get("case_id", "")


def _eligible_row(row: dict[str, str], cases_root: Path) -> tuple[bool, str]:
    case_id = row["case_id"]
    case_dir = cases_root / case_id
    if not case_dir.is_dir():
        return False, "case_dir_missing"
    for name in ("candidate_fsm.json", "oracle_suite.json", "reference_fsm.json"):
        if not (case_dir / name).is_file():
            return False, f"missing_{name}"
    try:
        bpr = float(row["initial_bpr"])
    except (KeyError, ValueError):
        return False, "invalid_initial_bpr"
    if bpr >= 1.0:
        return False, "bpr_not_below_one"
    return True, "eligible"


def build_inventory(
    rows: list[dict[str, str]],
    cases_root: Path,
    *,
    model_filter: str,
    repair_root: Path,
    reverify_bpr: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []

    for row in rows:
        case_id = row["case_id"]
        case_dir = cases_root / case_id
        ok, reason = _eligible_row(row, cases_root)
        candidate_path = case_dir / "candidate_fsm.json"
        oracle_path = case_dir / "oracle_suite.json"
        ref_path = case_dir / "reference_fsm.json"

        record: dict[str, Any] = {
            "case_id": case_id,
            "system_id": row.get("system_id"),
            "model_id": row.get("model_id"),
            "campaign_id": row.get("campaign_id"),
            "initial_bpr_csv": float(row["initial_bpr"]) if ok else None,
            "candidate_fsm_path": str(candidate_path),
            "oracle_suite_path": str(oracle_path),
            "reference_fsm_path": str(ref_path),
            "gold_available": ref_path.is_file(),
            "oracle_available": oracle_path.is_file(),
            "selection_reason": row.get("selection_reason"),
        }

        if not ok:
            record.update(
                structurally_valid=False,
                behaviourally_imperfect=False,
                eligible_for_iterative_probe=False,
                ineligibility_reason=reason,
            )
            inventory.append(record)
            continue

        fsm = load_json(candidate_path)
        struct_ok, struct_errors = check_structural_validity(fsm, repair_root)
        bpr = float(row["initial_bpr"])
        if reverify_bpr:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                report = score_fsm_paths(candidate_path, oracle_path, tmp_path)
                bpr = float(report["bpr"])
            finally:
                tmp_path.unlink(missing_ok=True)

        behaviourally_imperfect = bpr < 1.0
        probe_ok = (
            struct_ok
            and behaviourally_imperfect
            and oracle_path.is_file()
            and _model_matches(row, model_filter)
        )

        record.update(
            structurally_valid=struct_ok,
            structural_errors=struct_errors[:5] if struct_errors else [],
            initial_bpr=bpr,
            behaviourally_imperfect=behaviourally_imperfect,
            eligible_for_iterative_probe=probe_ok,
            ineligibility_reason=None if probe_ok else "filters",
        )
        inventory.append(record)
        if probe_ok:
            eligible.append(
                {
                    "case_id": case_id,
                    "case_dir": str(case_dir.resolve()),
                    "system_id": row.get("system_id"),
                    "model_id": row.get("model_id"),
                    "campaign_id": row.get("campaign_id"),
                    "candidate_fsm_path": str(candidate_path.resolve()),
                    "oracle_suite_path": str(oracle_path.resolve()),
                    "reference_fsm_path": str(ref_path.resolve()),
                    "requirement_path": str((case_dir / "requirement.json").resolve()),
                    "initial_bpr": bpr,
                    "structurally_valid": struct_ok,
                    "eligible": True,
                }
            )

    eligible.sort(key=lambda e: (e.get("system_id", ""), e["case_id"]))
    return inventory, eligible


def write_inventory_md(path: Path, inventory: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    lines = [
        "# Feasibility probe — candidate inventory",
        "",
        f"**Probe:** `{PROBE_ID}`",
        f"**Model filter:** `{manifest['model_filter']}`",
        f"**Manifest entries:** {len(manifest['entries'])}",
        "",
        "## Summary",
        "",
        f"- Rows inspected: {len(inventory)}",
        f"- Eligible for probe (model + structural + BPR<1): {manifest['eligible_count']}",
        "",
        "## Per-case inventory",
        "",
        "| case_id | model | initial_bpr | structural | BPR<1 | probe eligible |",
        "|---------|-------|-------------|------------|-------|----------------|",
    ]
    for r in inventory:
        bpr = r.get("initial_bpr", r.get("initial_bpr_csv"))
        bpr_s = f"{bpr:.4f}" if isinstance(bpr, (int, float)) else "—"
        lines.append(
            f"| {r['case_id']} | {r.get('model_id','')} | {bpr_s} | "
            f"{r.get('structurally_valid','')} | {r.get('behaviourally_imperfect','')} | "
            f"{r.get('eligible_for_iterative_probe','')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    cases_root = args.cases_root.resolve()
    csv_path = (args.selection_csv or cases_root / "candidate_selection_report.csv").resolve()
    repair_root = repair_repo_root()

    if not csv_path.is_file():
        print(f"error: selection CSV not found: {csv_path}", file=sys.stderr)
        return 2

    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    inventory, eligible = build_inventory(
        rows,
        cases_root,
        model_filter=args.model,
        repair_root=repair_root,
        reverify_bpr=args.reverify_bpr,
    )
    entries = eligible[: max(0, args.limit)]

    manifest = {
        "schema_version": "1.0.0",
        "probe_id": PROBE_ID,
        "scientific_question": (
            "Can iterative oracle-guided repair improve behavioural correctness of "
            "LLM-generated FSMs that are structurally acceptable but behaviourally incorrect?"
        ),
        "source": "ist2026b/paper/experiments/pilot_repair_cases_diverse",
        "model_filter": args.model,
        "repair_condition": "patch_trace_feedback",
        "eligible_count": len(eligible),
        "entries": entries,
    }

    out_manifest = args.output_manifest.resolve()
    write_json(out_manifest, manifest)

    if args.inventory_report:
        write_inventory_md(args.inventory_report.resolve(), inventory, manifest)

    print(
        json.dumps(
            {
                "manifest": str(out_manifest),
                "entries": len(entries),
                "eligible_total": len(eligible),
                "inventory_rows": len(inventory),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
