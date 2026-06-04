# Artifact scope — release v0.1.0

## What this release provides

Release **v0.1.0** (*Project scaffold and reproducibility policy*) defines the **public boundary** and directory layout for iterative oracle-guided repair studies. It is a citable software-project baseline for metadata and documentation only.

Included:

- Citation and Zenodo-oriented metadata (`CITATION.cff`, `.zenodo.json`)
- Reproducibility and release documentation
- Public/private boundary policy
- Placeholder directories for schemas, scripts, prompts, frozen experiments, environment, and tests

This release does **not** assert that iterative repair experiments have been executed or that any recovery rate has been measured.

## What this release does not include

- Large-scale or pilot **campaigns** with iteration budgets 0/1/3/5.
- **Frozen** `repair_run` records cited by a submitted paper.
- **Local model outputs** not required for Tier A audit replication.
- **Manuscript sources** or internal analysis notes.
- **Bundled frozen data** from prior Zenodo deposits unless a future release documents explicit import.

## Relationship to Zenodo and GitHub

- **Git tag `v0.1.0`** (when published) — Scaffold milestone; see [`RELEASE_NOTES_v0.1.0.md`](RELEASE_NOTES_v0.1.0.md).
- **Zenodo DOI** — Placeholder `10.5281/zenodo.TBD` until first deposit; update `CITATION.cff` after assignment.

## Future releases

Later versions may add:

- Iteration-aware orchestration and JSON schemas
- Frozen campaigns under `experiments/frozen/`
- Aggregated summaries and checksum manifests
- Tier A commands in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)

Each release will update this scope statement and release notes; v0.1.0 remains **documentation and layout only**.
