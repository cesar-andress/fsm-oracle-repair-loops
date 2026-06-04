# Iterative oracle-guided repair protocol (draft)

## Scientific object

Measure **behavioural recovery** under repeated oracle feedback for LLM-generated FSMs that pass
structural preconditions but fail behavioural thresholds.

Primary factor: **iteration budget** (e.g. 0, 1, 3, 5), not diagnostic-granularity contrasts.

## Loop shape

For each eligible candidate and iteration budget:

1. Score candidate against fixed oracle suite (\BPR{} and component outcomes).
2. If behavioural pass: terminate (success).
3. Project diagnostic from score report (deterministic).
4. Request constrained patch from LLM (or apply supplied patch in dry-run mode).
5. Validate patch; apply if accepted; update candidate.
6. Increment `iteration_index` until budget exhausted or terminal reached.

## Terminals

Record at minimum: complete repair, effective repair, regression, abstention, patch rejection,
and failure classes that block further progress.

## Frozen record contract

Each slot exports machine-readable runs (schema TBD under `schemas/`) suitable for Tier A
aggregation into `results/summaries/`.

## v0.1.0

Protocol text only; implementation and frozen exports pending.
