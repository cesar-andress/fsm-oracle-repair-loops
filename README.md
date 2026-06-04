# fsm-oracle-repair-loops

**Iterative oracle-guided repair of LLM-generated finite state machines — public research artifact.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Status:** v0.1.0 infrastructure scaffold — no frozen campaigns or empirical results yet.

## Author

| Field | Value |
|-------|--------|
| Name | César Andrés |
| ORCID | [0009-0001-8968-3404](https://orcid.org/0009-0001-8968-3404) |
| Email | [cesar.andress@ucjc.edu](mailto:cesar.andress@ucjc.edu) |
| Affiliation | CRIA-BDHS Research Group, Higher Polytechnic School of Technology and Science, Universidad Camilo José Cela, Madrid, Spain |

## Citation and archive (planned)

| Field | Value |
|-------|--------|
| Zenodo DOI | `10.5281/zenodo.TBD` (placeholder until first deposit) |
| Version | v0.1.0 |
| GitHub (planned) | [cesar-andress/fsm-oracle-repair-loops](https://github.com/cesar-andress/fsm-oracle-repair-loops) |

Machine-readable citation: [`CITATION.cff`](CITATION.cff)

## Purpose

Public artifact for empirical software engineering studies of **iterative oracle-guided repair**:
whether behavioural correctness of structurally acceptable LLM-generated FSMs can be recovered
through repeated diagnostic feedback, deterministic patch gates, and constrained repair loops.

This repository continues the line established by FSM-Bench-20, structural--behavioural correctness
evaluation, and single-iteration repair protocols — without bundling prior frozen campaigns by default.

## Quick links

| Document | Purpose |
|----------|---------|
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Reproduction tiers and commands (scaffold) |
| [`RELEASE_NOTES_v0.1.0.md`](RELEASE_NOTES_v0.1.0.md) | v0.1.0 scope |
| [`ARTIFACT_SCOPE.md`](ARTIFACT_SCOPE.md) | What this release includes / excludes |
| [`docs/repository_scope.md`](docs/repository_scope.md) | Public vs. private workspace roles |
| [`docs/PUBLIC_PRIVATE_BOUNDARY.md`](docs/PUBLIC_PRIVATE_BOUNDARY.md) | Boundary policy (mirrors paper doc) |

## Repository layout (scaffold)

| Path | Purpose |
|------|---------|
| [`schemas/`](schemas/) | JSON schemas (to be added with repair-loop contracts) |
| [`scripts/`](scripts/) | Deterministic scoring, diagnostics, iteration drivers |
| [`prompts/`](prompts/) | Frozen repair prompt templates |
| [`experiments/frozen/`](experiments/frozen/) | Frozen campaign exports cited by the paper |
| [`environment/`](environment/) | Python dependencies and run configuration |
| [`tests/`](tests/) | Schema and pipeline smoke tests |
| [`docs/`](docs/) | Study design and terminology |

## Requirements

**Python 3.12 or newer** (planned; see `environment/` when populated).

## Quick start (scaffold)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# pip install -r environment/requirements.txt   # when requirements.txt exists
# python -m pytest                              # when tests exist
```

Full commands will appear in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) after infrastructure lands.

## License

[MIT](LICENSE)

## Related workspace

Manuscript sources live in the sibling [`paper/`](../paper/) directory (internal, not part of this public tree).

## Policy note (`repo-externo`)

Project directory policy refers to this tree as **repo-externo**; the on-disk name is **`fsm-oracle-repair-loops`** to match the public GitHub/Zenodo repository name.
