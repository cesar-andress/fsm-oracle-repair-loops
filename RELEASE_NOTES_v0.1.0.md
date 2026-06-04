# Release notes — v0.1.0

**Title:** v0.1.0 — Project scaffold and reproducibility policy  
**Date:** 2026-06-04 (tag when published)

## Overview

This is the **initial public scaffold** of `fsm-oracle-repair-loops`, the companion artifact for an EMSE study on **iterative oracle-guided repair** of LLM-generated finite state machines.

This release establishes repository structure, metadata, licensing, citation files, and documentation boundaries. It does **not** publish empirical repair outcomes, frozen campaigns, or manuscript results.

See also: [`ARTIFACT_SCOPE.md`](ARTIFACT_SCOPE.md).

## Included in this release

| Area | Contents |
|------|----------|
| Metadata | `CITATION.cff`, `.zenodo.json`, `metadata.json` |
| Documentation | `README.md`, `REPRODUCIBILITY.md`, `ARTIFACT_SCOPE.md`, `docs/` |
| Policy | Public/private boundary, repository scope |
| Layout placeholders | `schemas/`, `scripts/`, `prompts/`, `experiments/frozen/`, `environment/`, `tests/` |
| License | MIT (`LICENSE`) |

## Not included in this release

- Frozen repair campaigns or iteration-budget study runs (0 / 1 / 3 / 5).
- Local model execution records (Ollama outputs, raw completions).
- Empirical summaries, LaTeX tables, or figures tied to reported outcomes.
- Manuscript LaTeX sources (maintained in private `paper/` workspace).
- Copied frozen data from FSM-Bench-20, `behavioral-fsm-benchmark`, or `fsm-repairability-study`.

## Reproducibility check

**v0.1.0:** No pytest suite or requirements file is required yet. Verify documentation only:

```bash
test -f CITATION.cff && test -f REPRODUCIBILITY.md && test -f LICENSE
```

When infrastructure lands, this section will reference `python -m pytest` and fixture-based smoke tests.

## Intended Zenodo archive contents (at first empirical freeze)

- Full git source tree at the release tag (schemas, scripts, docs, tests, frozen `experiments/frozen/` subset).
- Minimal public fixtures for validation only.
- **Excluded:** private `paper/` material, exploratory campaigns, author notes, and paths listed in [`.gitignore`](.gitignore).

After upload, replace `10.5281/zenodo.TBD` in `CITATION.cff` with the assigned DOI.

## Known limitations

- **No campaign data** — Cannot reproduce iteration-budget comparisons from this tag.
- **No scripts** — Scoring, iteration drivers, and table generators are not yet implemented.
- **Placeholder DOI** — Zenodo record not created; do not cite as published empirical evidence.
- **Scaffold manuscript** — Companion paper contains no reported results.

## Next planned releases

| Version | Intended scope |
|---------|----------------|
| v0.1.1+ | Core schemas, deterministic scoring/diagnostics, iteration-aware `repair_run` contract, pytest fixtures |
| v1.0.0+ | Frozen campaigns + Tier A reproduction for EMSE submission |

Until then, cite **v0.1.0** only as a project and policy baseline, not as study evidence.
