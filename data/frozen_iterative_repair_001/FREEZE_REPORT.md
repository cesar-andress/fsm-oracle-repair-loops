# Freeze report: frozen_iterative_repair_001

**Freeze date:** 2026-06-04

## Scope

Controlled multi-model extension of iterative oracle-guided FSM repair (45 cases, shared manifest).

**Scientific framing:** This freeze supports a study of failure modes and slot-level behavioural gains, not a model leaderboard.

## Protocol

| Parameter | Value |
|-----------|-------|
| Cases per model | 45 |
| Max iterations | 3 |
| Temperature | 0.0 |
| Repair condition | patch_trace_feedback |

## Sources

- **Input manifest:** `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_qwen7b` (copied as `manifest.json`)
- **Selection report:** same probe run as manifest (`selection_report.json`)
- **Comparison:** `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_extended_comparison`

## Included models

| Model key | Ollama tag | Source directory |
|-----------|------------|------------------|
| qwen7b | qwen2.5-coder:7b | `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_qwen7b` |
| qwen14b | qwen2.5-coder:14b | `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_qwen14b` |
| qwen32b | qwen2.5-coder:32b | `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_qwen32b` |
| llama8b | llama3.1:8b | `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_llama8b` |
| mistral12b | mistral-nemo:12b | `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_mistral12b` |
| gemma9b | gemma2:9b | `/home/cesar/papers/emse2026b/paper/experiments/iterative_repair_probe_003_45_gemma9b` |

## Per-model aggregates (effective = partial BPR gain, no complete repair)

| Model | Effective | Complete | Regressed |
|-------|-----------|----------|-----------|
| qwen7b | 3/45 | 0/45 | 4/45 |
| qwen14b | 5/45 | 0/45 | 0/45 |
| qwen32b | 9/45 | 0/45 | 0/45 |
| llama8b | 0/45 | 0/45 | 0/45 |
| mistral12b | 0/45 | 0/45 | 5/45 |
| gemma9b | 0/45 | 0/45 | 0/45 |

## Cross-model (45 shared cases)

- Improved by **at least one** model: **17/45**
- Improved by **none**: **28/45**
- Improved by **all** models: **0/45**
- Improved by **exactly one** model: **17/45**
- Complete repairs (any model): **0/45**

## Caveat

Gains are **slot-level** (individual repair cases), concentrated in specific **system × model** combinations (e.g. bike\_rental under smaller Qwen coders; elevator and warehouse/parking under larger Qwen). Patch-schema and patch-application failures dominate overall.

## Integrity

See `SHA256SUMS.txt` for copied JSON/CSV checksums. Raw run directories are referenced in `SOURCES.json` and were not modified.
