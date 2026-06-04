# fsm-oracle-repair-loops

Public, Zenodo-ready artifact for **iterative oracle-guided repair** of LLM-generated finite state machines, companion to the EMSE manuscript *When Oracle Feedback Is Not Enough: Failure Modes and Model-Specific Gains in Iterative LLM Repair of Behavioural FSMs*.

**Artifact version:** `v1.0.0`  
**License:** [MIT](LICENSE)

## What is included

- **Frozen evidence** — `data/frozen_iterative_repair_001/` (45 shared slots, six local repair models, three iterations at temperature 0)
- **Checksums** — `data/frozen_iterative_repair_001/SHA256SUMS.txt` and mirror `checksums/SHA256SUMS.txt`
- **Paper-ready tables** — `tables/*.tex`
- **Paper-ready figures** — `figures/*.pdf`
- **Scripts** — verify checksums, print summaries, regenerate tables/figures from the freeze

## What is not included

- Manuscript LaTeX, internal reviews, or submission portal files
- Raw per-case LLM transcripts or exploratory runs outside the freeze
- Ollama inference stack (results are pre-aggregated JSON/CSV only)
- Repair-case FSM JSON inputs (provenance paths in `SOURCES.json` only)

## Quickstart

```bash
cd fsm-oracle-repair-loops
python3 -m venv .venv && . .venv/bin/activate
pip install -r environment/requirements.txt

python3 scripts/verify_freeze.py
python3 scripts/summarize_freeze.py
python3 scripts/generate_paper_tables.py
python3 scripts/generate_paper_figures.py
```

## Expected key results (frozen_iterative_repair_001)

| Metric | Value |
|--------|-------|
| Shared repair slots | **45** |
| Repair models | **6** (qwen7b, qwen14b, qwen32b, llama8b, mistral12b, gemma9b) |
| Iterations | **3** (temperature **0**) |
| Effective repair | qwen7b **3**, qwen14b **5**, qwen32b **9**, llama8b **0**, mistral12b **0**, gemma9b **0** |
| Complete repair | **0** for every model |
| Cross-model | **17/45** improved by ≥1 model; **28/45** by none |

## Author

**César Andrés** — ORCID [0009-0001-8968-3404](https://orcid.org/0009-0001-8968-3404) — cesar.andress@ucjc.edu

## Citation

Zenodo DOI: **to be assigned** (placeholder). See [`CITATION.cff`](CITATION.cff) and [`docs/citation.md`](docs/citation.md).

## Documentation

| File | Purpose |
|------|---------|
| [`ARTIFACT_OVERVIEW.md`](ARTIFACT_OVERVIEW.md) | Data layout and paper mapping |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Step-by-step reproduction |
| [`RELEASE_NOTES_v1.0.0.md`](RELEASE_NOTES_v1.0.0.md) | Release changelog |
| [`metadata.json`](metadata.json) | Machine-readable artifact metadata |
