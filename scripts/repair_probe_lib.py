"""Shared utilities for the iterative oracle repair feasibility probe."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROBE_REPO_ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = PROBE_REPO_ROOT.parent.parent

DEFAULT_REPAIR_REPO = PAPERS_ROOT / "ist2026b" / "fsm-repairability-study"
DEFAULT_CASES_ROOT = (
    PAPERS_ROOT / "ist2026b" / "paper" / "experiments" / "pilot_repair_cases_diverse"
)
DEFAULT_SELECTION_CSV = DEFAULT_CASES_ROOT / "candidate_selection_report.csv"

REPAIR_CONDITION = "patch_trace_feedback"
DIAGNOSTIC_LEVEL = "trace"


def repair_repo_root() -> Path:
    raw = os.environ.get("FSM_REPAIR_REPO", "")
    return Path(raw).resolve() if raw else DEFAULT_REPAIR_REPO.resolve()


def ensure_repair_scripts_importable() -> Path:
    root = repair_repo_root()
    scripts = root / "scripts"
    if not scripts.is_dir():
        raise FileNotFoundError(f"repair study scripts not found: {scripts}")
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    return root


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def check_structural_validity(fsm: dict[str, Any], repair_root: Path) -> tuple[bool, list[str]]:
    ensure_repair_scripts_importable()
    from validate_fsm import validate_fsm_document, validate_referential_integrity  # noqa: E402

    schema_path = repair_root / "schemas" / "fsm.schema.json"
    schema = load_json(schema_path)
    errors = list(validate_fsm_document(fsm, schema))
    errors.extend(validate_referential_integrity(fsm))
    return len(errors) == 0, errors


def score_fsm_paths(
    fsm_path: Path,
    oracle_path: Path,
    output_path: Path,
    *,
    repair_root: Path | None = None,
) -> dict[str, Any]:
    repair_root = repair_root or repair_repo_root()
    ensure_repair_scripts_importable()
    from score_repair import score_fsm, write_report  # noqa: E402

    fsm = load_json(fsm_path)
    suite = load_json(oracle_path)
    report = score_fsm(
        fsm,
        suite,
        fsm_path=str(fsm_path),
        oracle_suite_path=str(oracle_path),
    )
    write_report(report, output_path)
    return report


def build_oracle_feedback(
    score_path: Path,
    *,
    case_id: str,
    run_id: str,
    iteration_index: int,
    output_path: Path,
    repair_root: Path | None = None,
) -> dict[str, Any]:
    repair_root = repair_root or repair_repo_root()
    ensure_repair_scripts_importable()
    from build_diagnostic import build_diagnostic, load_score_report, write_diagnostic  # noqa: E402

    report = load_score_report(score_path)
    doc = build_diagnostic(
        report,
        DIAGNOSTIC_LEVEL,
        case_id=case_id,
        run_id=run_id,
        iteration_index=iteration_index,
        score_report_path=score_path.resolve(),
        path_bases=[score_path.resolve().parent, repair_root],
    )
    write_diagnostic(doc, output_path)
    return doc


def apply_patch_paths(
    fsm_path: Path,
    patch_path: Path,
    output_fsm_path: Path,
    *,
    repair_root: Path | None = None,
) -> None:
    repair_root = repair_root or repair_repo_root()
    script = repair_root / "scripts" / "apply_patch.py"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--fsm",
            str(fsm_path),
            "--patch",
            str(patch_path),
            "-o",
            str(output_fsm_path),
        ],
        check=True,
        cwd=str(repair_root),
    )


def classify_iteration_outcome(
    bpr_before: float,
    bpr_after: float,
    *,
    patch_applied: bool,
    abstention: bool,
    patch_failure: bool,
    runner_failure: bool,
) -> dict[str, Any]:
    delta = bpr_after - bpr_before
    complete = bpr_after >= 1.0 - 1e-12
    effective = delta > 1e-12 and not complete
    regression = delta < -1e-12
    return {
        "bpr_before": bpr_before,
        "bpr_after": bpr_after,
        "delta_bpr": delta,
        "complete_repair": complete,
        "effective_repair": effective,
        "regression": regression,
        "abstention": abstention,
        "patch_application_failure": patch_failure,
        "runner_failure": runner_failure,
        "patch_applied": patch_applied,
    }


def resolve_case_paths(case_dir: Path) -> dict[str, Path]:
    return {
        "case_dir": case_dir,
        "case_json": case_dir / "case.json",
        "candidate_fsm": case_dir / "candidate_fsm.json",
        "oracle_suite": case_dir / "oracle_suite.json",
        "reference_fsm": case_dir / "reference_fsm.json",
        "requirement": case_dir / "requirement.json",
    }


def validate_manifest_entry(entry: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in (
        "case_id",
        "case_dir",
        "candidate_fsm_path",
        "oracle_suite_path",
    ):
        if key not in entry:
            issues.append(f"missing field: {key}")
    if "case_dir" in entry:
        case_dir = Path(entry["case_dir"])
        if not case_dir.is_dir():
            issues.append(f"case_dir not found: {case_dir}")
    for path_key in ("candidate_fsm_path", "oracle_suite_path"):
        if path_key in entry and not Path(entry[path_key]).is_file():
            issues.append(f"{path_key} not found: {entry[path_key]}")
    return issues
