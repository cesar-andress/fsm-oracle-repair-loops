# Artifact overview — v1.0.0

## Purpose

This repository publishes **frozen, checksum-backed aggregates** for the EMSE study of iterative oracle-guided repair on behavioural FSM slots. It supports verification and regeneration of paper tables/figures without re-running LLM inference.

## Frozen evidence (`data/frozen_iterative_repair_001/`)

| Path | Role |
|------|------|
| `manifest.json` | 45 shared repair slots (case IDs, initial BPR, structural eligibility) |
| `selection_report.json` | Slot selection metadata from the qwen7b probe run |
| `models/<key>/run_config.json` | Protocol per model (iterations, temperature, Ollama tag) |
| `models/<key>/analysis.json` | Per-model aggregates |
| `models/<key>/analysis_cases.csv` | Per-slot outcomes for one repair model |
| `comparison/comparison_analysis.json` | **Primary source** for paper numbers (per-model + cross-model) |
| `comparison/comparison_*.csv` | Tabular exports used to build LaTeX tables |
| `SOURCES.json` | Provenance paths to internal probe directories (read-only reference) |
| `FREEZE_REPORT.md` | Human-readable freeze summary |
| `SHA256SUMS.txt` | Integrity checksums for all bundled JSON/CSV files |

**Freeze ID:** `frozen_iterative_repair_001`

## Model runs (`models/`)

Six directories — `qwen7b`, `qwen14b`, `qwen32b`, `llama8b`, `mistral12b`, `gemma9b` — each holding aggregated results for the **same 45 slots** under identical protocol settings.

## Comparison outputs (`comparison/`)

- `comparison_analysis.json` — slot-level cross-model statistics (17/45 improved, 28/45 none, etc.)
- CSV companions for model summary, per-case matrix, and failure taxonomy

## Checksums

- **Canonical:** `data/frozen_iterative_repair_001/SHA256SUMS.txt`
- **Mirror:** `checksums/SHA256SUMS.txt` (identical content for reviewers)

Verify with `python3 scripts/verify_freeze.py`.

## Paper mapping

| Manuscript asset | Artifact path |
|------------------|---------------|
| Table: model summary | `tables/table_model_summary.tex` |
| Table: cross-model | `tables/table_cross_model_repairability.tex` |
| Table: failure taxonomy | `tables/table_failure_taxonomy_by_model.tex` |
| Table: system-specific gains | `tables/table_system_specific_gains.tex` |
| Figure: effective repairs | `figures/fig_effective_repairs_by_model.pdf` |
| Figure: failure taxonomy | `figures/fig_failure_taxonomy_by_model.pdf` |

Regenerate via `scripts/generate_paper_tables.py` and `scripts/generate_paper_figures.py`.

## Reproduction tiers

1. **Tier A (this release):** Verify checksums → read summaries → regenerate tables/figures.
2. **Tier B (out of scope):** Re-run Ollama repair probes (requires internal infrastructure; not redistributed).
