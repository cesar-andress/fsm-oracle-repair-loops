# Reproducibility — fsm-oracle-repair-loops v0.1.0

This document describes how to reproduce artefact outputs once the iterative repair
infrastructure and frozen campaigns exist. **Release v0.1.0 is a scaffold only:**
no empirical campaigns, frozen JSON summaries, or manuscript tables are shipped yet.

## Layout (sibling directories)

```text
emse2026b/
├── fsm-oracle-repair-loops/    ← REPO_ROOT (this repository; public / Zenodo)
└── paper/                      ← PAPER_ROOT (internal manuscript; not redistributed)
```

Use **relative** paths in commands and documentation. Do not embed workstation-specific absolute paths in published artefacts.

## Environment setup (when `environment/requirements.txt` exists)

```bash
export REPO_ROOT="path/to/fsm-oracle-repair-loops"
export PAPER_ROOT="path/to/paper"

cd "$REPO_ROOT"
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
python -m pytest
```

## Tier A — regenerate manuscript artefacts from frozen data (planned)

After frozen campaigns are deposited under `experiments/frozen/`:

1. Verify required summary files and run manifests (checklist TBD per campaign).
2. Run analysis scripts (to be added under `scripts/`) to emit JSON/CSV summaries.
3. Run table/figure generators with `--paper-root "$PAPER_ROOT"` when implemented.

**v0.1.0:** Steps above are not yet available; there is nothing to regenerate.

## Tier B — re-execute LLM repair loops (planned)

Optional re-execution with a local Ollama (or documented API) model will be described in
`docs/experimental_setup.md` when the iteration driver lands.

Re-runs are expected to differ stochastically from frozen records; Tier A remains the audit path for paper claims.

## Infrastructure smoke test (planned for v0.1.1+)

A minimal deterministic pipeline (score → diagnose → apply patch → record `repair_run` with
`iteration_index`) will be verified with fixtures under `tests/fixtures/` without network access.

## Citation

Until Zenodo deposit, cite the repository URL and version tag **v0.1.0** as infrastructure scaffold only — not as evidence of study outcomes.

After deposit, update this section with the assigned DOI (replace `10.5281/zenodo.TBD` in `CITATION.cff`).

## Related documents

- [`ARTIFACT_SCOPE.md`](ARTIFACT_SCOPE.md)
- [`RELEASE_NOTES_v0.1.0.md`](RELEASE_NOTES_v0.1.0.md)
- [`docs/citation.md`](docs/citation.md)
