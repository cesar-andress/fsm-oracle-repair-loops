# fsm-oracle-repair-loops

Public, Zenodo-ready artifact for **iterative oracle-guided repair** of LLM-generated finite state machines.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Working title (companion paper):** *Iterative Oracle-Guided Repair of LLM-Generated Finite State Machines: From Structural Acceptance to Behavioural Recovery* — target venue: **Empirical Software Engineering**.

**Status:** v0.1.0 scaffold — no frozen data or empirical results.

## Author

| Field | Value |
|-------|--------|
| Name | César Andrés |
| ORCID | [0009-0001-8968-3404](https://orcid.org/0009-0001-8968-3404) |
| Email | [cesar.andress@ucjc.edu](mailto:cesar.andress@ucjc.edu) |

## Documentation

| Document | Purpose |
|----------|---------|
| [`ARTIFACT_OVERVIEW.md`](ARTIFACT_OVERVIEW.md) | Scope, layout, reproduction tiers |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Commands (when infrastructure exists) |
| [`RELEASE_NOTES_v0.1.0.md`](RELEASE_NOTES_v0.1.0.md) | v0.1.0 changelog |
| [`docs/protocol.md`](docs/protocol.md) | Iterative repair protocol (draft) |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Field definitions (draft) |
| [`docs/citation.md`](docs/citation.md) | Citation text and BibTeX placeholder |
| [`CITATION.cff`](CITATION.cff) | Machine-readable metadata |

## Layout

```text
fsm-oracle-repair-loops/
├── data/frozen/       # publication freezes
├── data/examples/   # minimal public fixtures
├── results/         # summaries, tables, figures
├── scripts/ schemas/ prompts/ tests/
└── docs/
```

## Internal companion

Manuscript sources: [`../paper/`](../paper/) (not redistributed here). Planning: [`../contribution/`](../contribution/). Boundary policy: [`../contribution/PUBLIC_PRIVATE_BOUNDARY.md`](../contribution/PUBLIC_PRIVATE_BOUNDARY.md).

## License

[MIT](LICENSE)
