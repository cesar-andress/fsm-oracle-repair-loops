"""Shared paths and helpers for v1.0.0 artifact scripts (run from repo root)."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_DIR = REPO_ROOT / "data" / "frozen_iterative_repair_001"
COMPARISON_JSON = FREEZE_DIR / "comparison" / "comparison_analysis.json"
COMPARISON_CASES_CSV = FREEZE_DIR / "comparison" / "comparison_cases.csv"
CHECKSUMS_IN_FREEZE = FREEZE_DIR / "SHA256SUMS.txt"
CHECKSUMS_PUBLISHED = REPO_ROOT / "checksums" / "SHA256SUMS.txt"
TABLES_DIR = REPO_ROOT / "tables"
FIGURES_DIR = REPO_ROOT / "figures"

MODEL_ORDER = ["qwen7b", "qwen14b", "qwen32b", "llama8b", "mistral12b", "gemma9b"]

FAILURE_CLASSES = [
    "empty_patch",
    "duplicate_transition",
    "missing_transition_to_remove",
    "self_loop_rejected",
    "missing_state",
    "update_no_change",
    "invalid_patch_schema",
    "other_patch_application_failure",
]

FAILURE_ROW_SHORT = {
    "empty_patch": "empty",
    "duplicate_transition": "duplicate",
    "missing_transition_to_remove": "missing edge",
    "self_loop_rejected": "self-loop",
    "missing_state": "missing state",
    "update_no_change": "no-op update",
    "invalid_patch_schema": "schema",
    "other_patch_application_failure": "other apply",
}

SHORT_DOMINANT = {
    "empty_patch": "empty",
    "invalid_patch_schema": "schema",
    "duplicate_transition": "dup.",
    "missing_transition_to_remove": "missing edge",
    "self_loop_rejected": "self-loop",
    "missing_state": "missing state",
    "update_no_change": "no-op",
    "other_patch_application_failure": "other apply",
}


def load_comparison():
    with COMPARISON_JSON.open(encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dominant_failure_short(taxonomy):
    best_key, best_val = ("empty_patch", 0)
    for key, val in taxonomy.items():
        if val and val > best_val:
            best_key, best_val = key, val
    return SHORT_DOMINANT.get(best_key, best_key.replace("_", " "))


def write_table_model_summary(pm):
    lines = [
        "% Layout polish — numeric values from frozen_iterative_repair_001 (unchanged)",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Per-model outcomes on 45 shared slots.}",
        "\\label{tab:model-summary}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{2.5pt}",
        "\\begin{tabular}{@{}l@{\\hspace{1pt}}r@{\\hspace{1pt}}r@{\\hspace{1pt}}r@{\\hspace{1pt}}r@{\\hspace{1pt}}r@{\\hspace{1pt}}r@{\\hspace{1pt}}r@{\\hspace{1pt}}l@{}}",
        "\\toprule",
        "Model & $N$ & Eff. & Cmp. & Regr. & Init. & Best & Fin. & Fail. \\\\",
        "\\midrule",
    ]
    for key in MODEL_ORDER:
        m = pm[key]
        dom = dominant_failure_short(m["failure_taxonomy_normalized"])
        lines.append(
            f"{key} & {m['cases_attempted']} & "
            f"{m['cases_effective_repair_at_any_iteration']} & "
            f"{m['cases_complete_repair_at_any_iteration']} & "
            f"{m['cases_regressed_at_any_iteration']} & "
            f"{m['mean_initial_bpr']:.3f} & {m['mean_best_bpr']:.3f} & "
            f"{m['mean_final_bpr']:.3f} & {dom} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (TABLES_DIR / "table_model_summary.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_table_cross_model(cross):
    lines = [
        "% Layout polish — numeric values from frozen_iterative_repair_001 (unchanged)",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Cross-model slot outcomes on the shared 45-slot corpus.}",
        "\\label{tab:cross-model}",
        "\\small",
        "\\begin{tabular}{@{}lr@{}}",
        "\\toprule",
        "Outcome & Cases \\\\",
        "\\midrule",
        f"Improved by $\\geq$1 model & {cross['cases_improved_by_at_least_one_model']} \\\\",
        f"Improved by all models & {cross['cases_improved_by_all_models']} \\\\",
        f"Improved by exactly one model & {cross['cases_improved_only_by_one_model']} \\\\",
        f"No model improved & {cross['cases_where_no_model_improved']} \\\\",
        "Complete repair (BPR = 1.0) & 0 \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    (TABLES_DIR / "table_cross_model_repairability.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_table_failure_taxonomy(pm):
    lines = [
        "% Layout polish — numeric values from frozen_iterative_repair_001 (unchanged)",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Failure-event counts by repair model (row abbreviations).}",
        "\\label{tab:failure-taxonomy}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{1.05}",
        "\\begin{tabular}{@{}l@{\\hspace{2pt}}*{6}{r@{\\hspace{2pt}}}@{}}",
        "\\toprule",
        "Failure & " + " & ".join(MODEL_ORDER) + " \\\\",
        "\\midrule",
    ]
    for cls in FAILURE_CLASSES:
        counts = [pm[m]["failure_taxonomy_normalized"].get(cls, 0) for m in MODEL_ORDER]
        if sum(counts) == 0:
            continue
        lines.append(FAILURE_ROW_SHORT[cls] + " & " + " & ".join(str(c) for c in counts) + " \\\\")
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "",
            "\\medskip",
            "{\\footnotesize",
            "\\textit{Note.}",
            "Row labels abbreviate canonical failure classes:",
            "\\begin{itemize}[leftmargin=1.2em,itemsep=0pt,topsep=2pt,parsep=0pt]",
            "  \\item empty $\\rightarrow$ \\texttt{empty\\_patch}",
            "  \\item schema $\\rightarrow$ \\texttt{invalid\\_patch\\_schema}",
            "  \\item duplicate $\\rightarrow$ \\texttt{duplicate\\_transition}",
            "  \\item missing edge $\\rightarrow$ \\texttt{missing\\_transition\\_to\\_remove}",
            "  \\item self-loop $\\rightarrow$ \\texttt{self\\_loop\\_rejected}",
            "  \\item missing state $\\rightarrow$ \\texttt{missing\\_state}",
            "  \\item no-op update $\\rightarrow$ \\texttt{update\\_no\\_change}",
            "  \\item other apply $\\rightarrow$ \\texttt{other\\_patch\\_application\\_failure}",
            "\\end{itemize}",
            "}",
            "\\end{table}",
            "",
        ]
    )
    (TABLES_DIR / "table_failure_taxonomy_by_model.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_table_system_specific():
    with COMPARISON_CASES_CSV.open(encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    stats = defaultdict(lambda: {"slots": 0, "max_delta": 0.0})
    for row in cases:
        sid = row["system_id"]
        for mk in MODEL_ORDER:
            if row.get(f"{mk}_improved_any", "").strip().lower() != "true":
                continue
            stats[(sid, mk)]["slots"] += 1
            try:
                d = float(row.get(f"{mk}_delta_best_vs_initial") or 0)
            except ValueError:
                d = 0.0
            if d > stats[(sid, mk)]["max_delta"]:
                stats[(sid, mk)]["max_delta"] = d

    lines = [
        "% Layout polish — numeric values from frozen_iterative_repair_001 (unchanged)",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Systems with at least one effective repair slot.}",
        "\\label{tab:system-gains}",
        "\\small",
        "\\setlength{\\tabcolsep}{5pt}",
        "\\begin{tabular}{@{}l l r r@{}}",
        "\\toprule",
        "System & Model & Slots & Max $\\Delta$BPR \\\\",
        "\\midrule",
    ]
    for (sid, mk) in sorted(stats.keys()):
        info = stats[(sid, mk)]
        sid_tex = sid.replace("_", "\\_")
        lines.append(
            f"{sid_tex} & {mk} & {info['slots']} & {info['max_delta']:.3f} \\\\"
        )
    if not stats:
        lines.append("\\multicolumn{4}{c}{No system-level gains} \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (TABLES_DIR / "table_system_specific_gains.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_all_tables():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    comp = load_comparison()
    pm = comp["per_model"]
    cross = comp["cross_model"]
    write_table_model_summary(pm)
    write_table_cross_model(cross)
    write_table_failure_taxonomy(pm)
    write_table_system_specific()
    return list(TABLES_DIR.glob("table_*.tex"))


def write_all_figures():
    import matplotlib.pyplot as plt

    comp = load_comparison()
    pm = comp["per_model"]
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    effective = [pm[k]["cases_effective_repair_at_any_iteration"] for k in MODEL_ORDER]
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.bar(range(len(MODEL_ORDER)), effective, color="0.35", edgecolor="0.15", linewidth=0.6)
    ax.set_xticks(range(len(MODEL_ORDER)))
    ax.set_xticklabels(MODEL_ORDER, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Effective repair slots")
    ax.set_ylim(0, max(effective + [10]) * 1.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.subplots_adjust(bottom=0.22)
    p1 = FIGURES_DIR / "fig_effective_repairs_by_model.pdf"
    fig.savefig(p1)
    plt.close(fig)

    top_classes = [
        c
        for c in FAILURE_CLASSES
        if sum(pm[m]["failure_taxonomy_normalized"].get(c, 0) for m in MODEL_ORDER) > 0
    ]
    data = {
        c: [pm[m]["failure_taxonomy_normalized"].get(c, 0) for m in MODEL_ORDER]
        for c in top_classes
    }
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    bottoms = [0] * len(MODEL_ORDER)
    n = len(top_classes)
    greys = [str(0.2 + 0.6 * i / max(n - 1, 1)) for i in range(n)]
    short = {
        "empty_patch": "empty",
        "duplicate_transition": "duplicate",
        "missing_transition_to_remove": "missing edge",
        "self_loop_rejected": "self-loop",
        "missing_state": "missing state",
        "update_no_change": "no-op update",
        "invalid_patch_schema": "schema",
        "other_patch_application_failure": "other apply",
    }
    for cls, grey in zip(top_classes, greys):
        vals = data[cls]
        ax.bar(
            range(len(MODEL_ORDER)),
            vals,
            bottom=bottoms,
            label=short.get(cls, cls),
            color=grey,
            edgecolor="0.2",
            linewidth=0.4,
        )
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xticks(range(len(MODEL_ORDER)))
    ax.set_xticklabels(MODEL_ORDER, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Failure events")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=4,
        fontsize=8,
        frameon=False,
        columnspacing=1.2,
        handlelength=1.2,
    )
    fig.subplots_adjust(bottom=0.28)
    p2 = FIGURES_DIR / "fig_failure_taxonomy_by_model.pdf"
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)

    return [p1, p2]
