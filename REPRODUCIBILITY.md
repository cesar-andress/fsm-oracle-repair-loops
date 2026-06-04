# Reproducibility — fsm-oracle-repair-loops

## Layout

```text
emse2026b/
├── fsm-oracle-repair-loops/   # REPO_ROOT (this repository)
├── paper/                     # PAPER_ROOT (internal manuscript)
└── contribution/              # planning (non-public by default)
```

Use environment variables with **your** checkout paths—never commit absolute local paths.

## v0.1.0

No frozen data, Python package, or pytest suite is required yet. Verify scaffold files:

```bash
cd path/to/fsm-oracle-repair-loops
test -f CITATION.cff && test -f metadata.json && test -f docs/protocol.md
```

## Tier A (planned)

After `data/frozen/` is populated:

1. Install Python 3.12+ environment from future `environment/requirements.txt` or `pyproject.toml`.
2. Run `pytest` on public fixtures under `data/examples/`.
3. Execute analysis scripts in `scripts/` to refresh `results/summaries/`.
4. Regenerate `results/tables/` and `results/figures/` for the companion `paper/` tree.

## Tier B (planned)

Optional Ollama-backed re-execution of iterative repair loops; outputs will differ from frozen LLM bytes.

## Manuscript alignment

Export only records cited in the EMSE manuscript. Document checksums in release notes before tagging.

## Citation

Replace `10.5281/zenodo.TBD` in `CITATION.cff` after Zenodo deposit.
