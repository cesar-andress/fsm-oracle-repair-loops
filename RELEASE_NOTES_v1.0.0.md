# Release notes — v1.0.0

**Date:** 2026-06-04  
**Tag:** `v1.0.0`  
**Companion paper:** *When Oracle Feedback Is Not Enough: Failure Modes and Model-Specific Gains in Iterative LLM Repair of Behavioural FSMs*

## Added

- Frozen evidence bundle `data/frozen_iterative_repair_001/` (manifest, selection report, six model aggregates, cross-model comparison, `SOURCES.json`, `FREEZE_REPORT.md`, `SHA256SUMS.txt`)
- Paper-ready LaTeX tables in `tables/`
- Paper-ready PDF figures in `figures/`
- Scripts: `verify_freeze.py`, `summarize_freeze.py`, `generate_paper_tables.py`, `generate_paper_figures.py`
- Published checksum mirror: `checksums/SHA256SUMS.txt`
- Documentation: `README.md`, `ARTIFACT_OVERVIEW.md`, `REPRODUCIBILITY.md`, `metadata.json`, `CITATION.cff`

## Key results (unchanged from internal freeze)

- 45 shared repair slots; 6 repair models; 3 iterations at T=0
- Effective repair: 3 / 5 / 9 / 0 / 0 / 0 (qwen7b → gemma9b)
- Complete repair: 0/45 for all models
- Cross-model: 17/45 improved by ≥1 model; 28/45 by none

## Zenodo archive

- **DOI:** [10.5281/zenodo.20548450](https://doi.org/10.5281/zenodo.20548450)
- **Version:** v1.0.0 (2026-06-04)

## Not in this release

- Raw LLM run logs or case-level FSM inputs (see `SOURCES.json` provenance only)

## Replaces

- v0.1.0 scaffold (no empirical freeze)
