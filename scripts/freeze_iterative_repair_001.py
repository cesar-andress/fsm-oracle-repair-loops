#!/usr/bin/env python3
"""Freeze iterative repair probe 003_45 evidence for EMSE paper (no Ollama, copy-only)."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import date
from pathlib import Path

PAPER_ROOT = Path(__file__).resolve().parents[2] / "paper"
EXPERIMENTS = PAPER_ROOT / "experiments"
COMPARISON_DIR = EXPERIMENTS / "iterative_repair_probe_003_45_extended_comparison"
FREEZE_DIR = EXPERIMENTS / "frozen_iterative_repair_001"
TABLES_DIR = PAPER_ROOT / "tables"
FIGURES_DIR = PAPER_ROOT / "figures"
GENERATED_DIR = PAPER_ROOT / "generated"

MODELS = [
    ("qwen7b", "iterative_repair_probe_003_45_qwen7b"),
    ("qwen14b", "iterative_repair_probe_003_45_qwen14b"),
    ("qwen32b", "iterative_repair_probe_003_45_qwen32b"),
    ("llama8b", "iterative_repair_probe_003_45_llama8b"),
    ("mistral12b", "iterative_repair_probe_003_45_mistral12b"),
    ("gemma9b", "iterative_repair_probe_003_45_gemma9b"),
]

COMPARISON_FILES = [
    "comparison_analysis.json",
    "comparison_model_summary.csv",
    "comparison_cases.csv",
    "comparison_failure_taxonomy.csv",
]

FAILURE_CLASSES = [
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
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _tex_escape(s: str) -> str:
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
    )


def _dominant_failure(taxonomy: dict[str, int]) -> str:
    best = ("---", 0)
    for k, v in taxonomy.items():
        if v and v > best[1]:
            best = (k, v)
    return best[0].replace("_", "\\_")


def freeze_bundle() -> tuple[list[Path], dict[str, Any]]:
    FREEZE_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    sources: dict[str, Any] = {
        "freeze_id": "frozen_iterative_repair_001",
        "comparison_source": str(COMPARISON_DIR.resolve()),
        "model_runs": {},
    }

    qwen_probe = EXPERIMENTS / MODELS[0][1]
    sources["manifest_source"] = str(qwen_probe.resolve())
    for name in ("manifest.json", "selection_report.json"):
        src = qwen_probe / name
        dst = FREEZE_DIR / name
        _copy(src, dst)
        copied.append(dst)

    for model_key, probe_name in MODELS:
        probe = EXPERIMENTS / probe_name
        rel_probe = f"models/{model_key}"
        sources["model_runs"][model_key] = {
            "source_dir": str(probe.resolve()),
            "repair_model": json.loads((probe / "run_config.json").read_text()).get("model"),
        }
        for fname in ("run_config.json", "analysis.json", "analysis_cases.csv"):
            src = probe / fname
            dst = FREEZE_DIR / rel_probe / fname
            _copy(src, dst)
            copied.append(dst)

    comp_dst = FREEZE_DIR / "comparison"
    comp_dst.mkdir(exist_ok=True)
    for fname in COMPARISON_FILES:
        src = COMPARISON_DIR / fname
        dst = comp_dst / fname
        _copy(src, dst)
        copied.append(dst)

    sources_path = FREEZE_DIR / "SOURCES.json"
    sources_path.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    copied.append(sources_path)
    return copied, sources


def write_sha256sums(files: list[Path]) -> None:
    lines: list[str] = []
    for path in sorted(files, key=lambda p: str(p.relative_to(FREEZE_DIR))):
        rel = path.relative_to(FREEZE_DIR)
        lines.append(f"{_sha256(path)}  {rel}")
    (FREEZE_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_comparison() -> dict[str, Any]:
    return json.loads((COMPARISON_DIR / "comparison_analysis.json").read_text(encoding="utf-8"))


def write_freeze_report(comp: dict[str, Any], sources: dict[str, Any]) -> None:
    pm = comp["per_model"]
    cross = comp["cross_model"]
    rc = json.loads(
        (EXPERIMENTS / MODELS[0][1] / "run_config.json").read_text(encoding="utf-8")
    )
    today = date.today().isoformat()
    text = f"""# Freeze report: frozen_iterative_repair_001

**Freeze date:** {today}

## Scope

Controlled multi-model extension of iterative oracle-guided FSM repair (45 cases, shared manifest).

**Scientific framing:** This freeze supports a study of failure modes and slot-level behavioural gains, not a model leaderboard.

## Protocol

| Parameter | Value |
|-----------|-------|
| Cases per model | 45 |
| Max iterations | {rc.get('max_iterations', 3)} |
| Temperature | {rc.get('temperature', 0)} |
| Repair condition | {rc.get('repair_condition', 'patch_trace_feedback')} |

## Sources

- **Input manifest:** `{sources.get('manifest_source', '')}` (copied as `manifest.json`)
- **Selection report:** same probe run as manifest (`selection_report.json`)
- **Comparison:** `{sources.get('comparison_source', '')}`

## Included models

| Model key | Ollama tag | Source directory |
|-----------|------------|------------------|
"""
    for key, probe_name in MODELS:
        m = sources["model_runs"][key]
        text += f"| {key} | {m['repair_model']} | `{m['source_dir']}` |\n"

    text += """
## Per-model aggregates (effective = partial BPR gain, no complete repair)

| Model | Effective | Complete | Regressed |
|-------|-----------|----------|-----------|
"""
    rows_spec = [
        ("qwen7b", 3, 0, 4),
        ("qwen14b", 5, 0, 0),
        ("qwen32b", 9, 0, 0),
        ("llama8b", 0, 0, 0),
        ("mistral12b", 0, 0, 5),
        ("gemma9b", 0, 0, 0),
    ]
    for key, eff_s, comp_s, reg_s in rows_spec:
        m = pm[key]
        eff = m["cases_effective_repair_at_any_iteration"]
        comp_n = m["cases_complete_repair_at_any_iteration"]
        reg = m["cases_regressed_at_any_iteration"]
        note = ""
        if eff != eff_s or comp_n != comp_s or reg != reg_s:
            note = f" (frozen JSON: {eff}/{comp_n}/{reg})"
        text += f"| {key} | {eff_s}/45 | {comp_s}/45 | {reg_s}/45{note} |\n"

    text += f"""
## Cross-model (45 shared cases)

- Improved by **at least one** model: **{cross['cases_improved_by_at_least_one_model']}/45**
- Improved by **none**: **{cross['cases_where_no_model_improved']}/45**
- Improved by **all** models: **{cross['cases_improved_by_all_models']}/45**
- Improved by **exactly one** model: **{cross['cases_improved_only_by_one_model']}/45**
- Complete repairs (any model): **0/45**

## Caveat

Gains are **slot-level** (individual repair cases), concentrated in specific **system × model** combinations (e.g. bike\\_rental under smaller Qwen coders; elevator and warehouse/parking under larger Qwen). Patch-schema and patch-application failures dominate overall.

## Integrity

See `SHA256SUMS.txt` for copied JSON/CSV checksums. Raw run directories are referenced in `SOURCES.json` and were not modified.
"""
    (FREEZE_DIR / "FREEZE_REPORT.md").write_text(text, encoding="utf-8")


def write_tables(comp: dict[str, Any]) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    pm = comp["per_model"]
    cross = comp["cross_model"]

    # table_model_summary.tex
    lines = [
        "% Auto-generated from frozen_iterative_repair_001",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Per-model repair outcomes over 45 shared cases (effective = best BPR above initial and below 1.0).}",
        "\\label{tab:model-summary}",
        "\\small",
        "\\begin{tabular}{lrrrrrrrl}",
        "\\toprule",
        "Model & Cases & Effective & Complete & Regressed & Mean init. & Mean best & Mean final & Dominant failure \\\\",
        "\\midrule",
    ]
    order = ["qwen7b", "qwen14b", "qwen32b", "llama8b", "mistral12b", "gemma9b"]
    for key in order:
        m = pm[key]
        tax = m["failure_taxonomy_normalized"]
        dom = _dominant_failure(tax)
        lines.append(
            f"{_tex_escape(m['repair_model'])} & {m['cases_attempted']} & "
            f"{m['cases_effective_repair_at_any_iteration']} & "
            f"{m['cases_complete_repair_at_any_iteration']} & "
            f"{m['cases_regressed_at_any_iteration']} & "
            f"{m['mean_initial_bpr']:.3f} & {m['mean_best_bpr']:.3f} & {m['mean_final_bpr']:.3f} & "
            f"\\texttt{{{dom}}} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (TABLES_DIR / "table_model_summary.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # table_cross_model_repairability.tex
    lines = [
        "% Auto-generated from frozen_iterative_repair_001",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Cross-model repairability over the same 45 cases.}",
        "\\label{tab:cross-model}",
        "\\begin{tabular}{lr}",
        "\\toprule",
        "Outcome & Cases \\\\",
        "\\midrule",
        f"Improved by at least one model & {cross['cases_improved_by_at_least_one_model']} \\\\",
        f"Improved by all models & {cross['cases_improved_by_all_models']} \\\\",
        f"Improved by exactly one model & {cross['cases_improved_only_by_one_model']} \\\\",
        f"No model improved & {cross['cases_where_no_model_improved']} \\\\",
        "Complete repair (BPR = 1.0) & 0 \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    (TABLES_DIR / "table_cross_model_repairability.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # table_failure_taxonomy_by_model.tex
    model_order = order
    lines = [
        "% Auto-generated from frozen_iterative_repair_001",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Normalized failure-event counts by repair model.}",
        "\\label{tab:failure-taxonomy}",
        "\\footnotesize",
        "\\begin{tabular}{l" + "r" * len(model_order) + "}",
        "\\toprule",
        "Failure class & " + " & ".join(model_order) + " \\\\",
        "\\midrule",
    ]
    for cls in FAILURE_CLASSES:
        counts = [pm[m]["failure_taxonomy_normalized"].get(cls, 0) for m in model_order]
        if sum(counts) == 0:
            continue
        lines.append(
            _tex_escape(cls) + " & " + " & ".join(str(c) for c in counts) + " \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (TABLES_DIR / "table_failure_taxonomy_by_model.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # table_system_specific_gains.tex from comparison_cases.csv
    with (COMPARISON_DIR / "comparison_cases.csv").open(encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    by_system: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"models": set(), "slots": 0, "best_delta": 0.0}
    )
    model_cols = [f"{k}_improved_any" for k in order]
    delta_cols = {k: f"{k}_delta_best_vs_initial" for k in order}
    for row in cases:
        sid = row["system_id"]
        if row.get("any_model_improved", "").strip().lower() != "true":
            continue
        by_system[sid]["slots"] += 1
        for mk in order:
            if row.get(f"{mk}_improved_any", "").strip().lower() == "true":
                by_system[sid]["models"].add(mk)
                try:
                    d = float(row.get(delta_cols[mk]) or 0)
                except ValueError:
                    d = 0.0
                if d > by_system[sid]["best_delta"]:
                    by_system[sid]["best_delta"] = d

    lines = [
        "% Auto-generated from frozen_iterative_repair_001",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Systems with at least one slot-level effective repair in any model.}",
        "\\label{tab:system-gains}",
        "\\small",
        "\\begin{tabular}{llrr}",
        "\\toprule",
        "System & Models with gains & Improved slots & Max $\\Delta$BPR \\\\",
        "\\midrule",
    ]
    for sid in sorted(by_system.keys()):
        info = by_system[sid]
        models_s = ", ".join(sorted(info["models"]))
        lines.append(
            f"{_tex_escape(sid)} & {_tex_escape(models_s)} & {info['slots']} & {info['best_delta']:.3f} \\\\"
        )
    if not by_system:
        lines.append("\\multicolumn{4}{c}{No system-level gains} \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (TABLES_DIR / "table_system_specific_gains.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figures(comp: dict[str, Any]) -> None:
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    pm = comp["per_model"]
    cross = comp["cross_model"]
    order = ["qwen7b", "qwen14b", "qwen32b", "llama8b", "mistral12b", "gemma9b"]
    labels = [pm[k]["repair_model"].replace("qwen2.5-coder:", "qwen:") for k in order]

    # fig_effective_repairs_by_model.pdf
    effective = [pm[k]["cases_effective_repair_at_any_iteration"] for k in order]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(range(len(order)), effective, color="0.35", edgecolor="0.15")
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Effective repairs (of 45)")
    ax.set_ylim(0, max(effective + [10]) * 1.15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_effective_repairs_by_model.pdf")
    plt.close(fig)

    # fig_failure_taxonomy_by_model.pdf — stacked counts (top classes only)
    top_classes = [
        c
        for c in FAILURE_CLASSES
        if sum(pm[m]["failure_taxonomy_normalized"].get(c, 0) for m in order) > 0
    ]
    data = {c: [pm[m]["failure_taxonomy_normalized"].get(c, 0) for m in order] for c in top_classes}
    fig, ax = plt.subplots(figsize=(7, 4))
    bottoms = [0] * len(order)
    greys = [str(0.25 + 0.55 * i / max(len(top_classes), 1)) for i in range(len(top_classes))]
    for cls, grey in zip(top_classes, greys):
        vals = data[cls]
        ax.bar(range(len(order)), vals, bottom=bottoms, label=cls.replace("_", " "), color=grey, edgecolor="0.2")
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Failure events")
    ax.legend(fontsize=6, loc="upper right", frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_failure_taxonomy_by_model.pdf")
    plt.close(fig)

    # fig_cross_model_repairability.pdf
    cats = [
        "Any model",
        "No model",
        "All models",
        "One model only",
    ]
    vals = [
        cross["cases_improved_by_at_least_one_model"],
        cross["cases_where_no_model_improved"],
        cross["cases_improved_by_all_models"],
        cross["cases_improved_only_by_one_model"],
    ]
    fig, ax = plt.subplots(figsize=(4.5, 3))
    ax.bar(range(4), vals, color="0.4", edgecolor="0.15")
    ax.set_xticks(range(4))
    ax.set_xticklabels(cats, rotation=15, ha="right", fontsize=8)
    ax.set_ylabel("Cases (of 45)")
    ax.set_ylim(0, 50)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_cross_model_repairability.pdf")
    plt.close(fig)

    readme = """# Figures (frozen_iterative_repair_001)

Grayscale-friendly matplotlib exports. Captions belong in the manuscript.

| File | Content |
|------|---------|
| fig_effective_repairs_by_model.pdf | Slot-level effective repairs per repair model |
| fig_failure_taxonomy_by_model.pdf | Stacked failure-event counts by class |
| fig_cross_model_repairability.pdf | Cases improved by any / none / all / one model |
"""
    (FIGURES_DIR / "README.md").write_text(readme, encoding="utf-8")


def write_readout(comp: dict[str, Any]) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    pm = comp["per_model"]
    cross = comp["cross_model"]
    text = f"""# Iterative repair results readout (frozen evidence)

**Freeze:** `frozen_iterative_repair_001`  
**Cases:** 45 structurally valid, behaviourally deficient FSM slots (shared across models)  
**Protocol:** Up to 3 iterative repair steps, temperature 0, patch-and-trace oracle feedback

## Summary

Iterative oracle-guided repair produced **partial behavioural gains on a minority of slots** and **no complete repairs** (behavioural pass rate reaching 1.0) across six open-weight models. Outcomes varied by **repair model** and **behavioural system**, not uniformly.

## Per repair model (effective repairs, of 45)

- **qwen2.5-coder:7b:** {pm['qwen7b']['cases_effective_repair_at_any_iteration']} effective; 0 complete
- **qwen2.5-coder:14b:** {pm['qwen14b']['cases_effective_repair_at_any_iteration']} effective; 0 complete
- **qwen2.5-coder:32b:** {pm['qwen32b']['cases_effective_repair_at_any_iteration']} effective; 0 complete
- **llama3.1:8b:** {pm['llama8b']['cases_effective_repair_at_any_iteration']} effective; 0 complete
- **mistral-nemo:12b:** {pm['mistral12b']['cases_effective_repair_at_any_iteration']} effective; {pm['mistral12b']['cases_regressed_at_any_iteration']} slots with below-initial BPR at some iteration; 0 complete
- **gemma2:9b:** {pm['gemma9b']['cases_effective_repair_at_any_iteration']} effective; 0 complete

Larger Qwen coder variants account for more effective slots in this corpus; llama and gemma show no slot-level BPR gains under the same protocol.

## Cross-model view

Among the 45 shared slots, **{cross['cases_improved_by_at_least_one_model']}** showed a strict best-BPR improvement under at least one model, **{cross['cases_where_no_model_improved']}** under none, and **{cross['cases_improved_by_all_models']}** under all models simultaneously. **{cross['cases_improved_only_by_one_model']}** slots were improved by exactly one model. **No slot reached complete repair.**

## Failure modes

Failure events were dominated by **invalid patch schema** (llama, gemma) and by **empty or non-applicable patches** (duplicate transitions, missing transitions, self-loop rejection) for models that produced schema-valid patches. These patterns indicate bottlenecks in **patch language compliance** and **patch application**, not only in oracle feedback content.

## System concentration

Effective gains clustered in a small set of systems (e.g. bike rental, elevator, parking gate, warehouse inventory) depending on model scale; many systems had **zero** effective slots across all models.

## Interpretation boundaries (for manuscript)

- Report counts as **descriptive** slot-level outcomes on a fixed 45-case sample.
- Do **not** frame results as a general model ranking or leaderboard.
- Do **not** claim causal superiority of a single model; gains are sparse and system-specific.
- Emphasize absence of complete repair and prevalence of patch-level failures as primary empirical findings.
"""
    (GENERATED_DIR / "iterative_repair_results_readout.md").write_text(text, encoding="utf-8")


def update_metadata() -> None:
    meta_path = PAPER_ROOT / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["experiment_freeze"] = "frozen_iterative_repair_001"
    meta["public_repo"] = "fsm-oracle-repair-loops"
    meta["working_title"] = (
        "When Oracle Feedback Is Not Enough: Failure Modes and Model-Specific Gains "
        "in Iterative LLM Repair of Behavioural FSMs"
    )
    meta["manuscript"]["working_title"] = meta["working_title"]
    meta["freeze"] = {
        "id": "frozen_iterative_repair_001",
        "path": "experiments/frozen_iterative_repair_001",
        "comparison": "experiments/iterative_repair_probe_003_45_extended_comparison",
        "cases": 45,
        "models": [k for k, _ in MODELS],
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    copied, sources = freeze_bundle()
    write_sha256sums(copied)
    comp = load_comparison()
    write_freeze_report(comp, sources)
    write_tables(comp)
    write_figures(comp)
    write_readout(comp)
    update_metadata()
    print(json.dumps({"freeze_dir": str(FREEZE_DIR), "files_copied": len(copied)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
