# Artifact overview — fsm-oracle-repair-loops v0.1.0

## Repository purpose

**fsm-oracle-repair-loops** supports empirical software engineering studies of **iterative
oracle-guided repair**: repeated score--diagnose--patch--validate loops on structurally
acceptable yet behaviourally deficient LLM-generated FSMs.

This is **not**:

- a diagnostic-granularity (C/D/E) primary study;
- a new FSM generation benchmark release;
- a model leaderboard.

It **builds on** prior benchmark, structural--behavioural correctness, and single-iteration repair
protocol work by adding **iteration-budget** measurement and frozen loop records.

## Author

| Field | Value |
|-------|--------|
| Name | César Andrés |
| ORCID | [0009-0001-8968-3404](https://orcid.org/0009-0001-8968-3404) |
| Email | cesar.andress@ucjc.edu |

## v0.1.0 contents

| Area | Status |
|------|--------|
| Metadata (`CITATION.cff`, `metadata.json`, `.zenodo.json`) | Present |
| Documentation (`docs/`, `REPRODUCIBILITY.md`, release notes) | Present |
| Directory layout (`data/`, `results/`, `scripts/`, …) | Scaffold only |
| Frozen campaigns | **Not included** |
| Empirical summaries | **Not included** |

## Planned frozen layout

| Path | Role |
|------|------|
| `data/frozen/` | Campaign exports cited by the EMSE manuscript |
| `data/examples/` | Minimal synthetic fixtures for schema smoke tests |
| `results/summaries/` | Aggregated JSON/CSV readouts |
| `results/tables/` | LaTeX or CSV for manuscript tables |
| `results/figures/` | PDF or source for manuscript figures |

## Reproduction tiers (planned)

**Tier A** — Regenerate summaries, tables, and figures from `data/frozen/` without re-invoking the LLM.

**Tier B** — Optional re-execution of repair loops (documented stochastic divergence from freezes).

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

## Companion paper

Internal manuscript: `../paper/` (Empirical Software Engineering).

## Citation

Use [`CITATION.cff`](CITATION.cff). At v0.1.0 cite as **infrastructure scaffold only**, not as empirical evidence.
