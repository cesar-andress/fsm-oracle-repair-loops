# Study design (draft)

**Status:** Design scaffold — not frozen.

## Research focus

Iterative oracle-guided repair of LLM-generated FSMs that are structurally acceptable yet behaviourally deficient under fixed oracle suites.

## Planned iteration budgets

| Budget | Role |
|--------|------|
| 0 | Baseline (no repair loop) |
| 1 | Single-iteration comparison to prior protocol line |
| 3 | Short iterative loop |
| 5 | Extended iterative loop |

## Planned readouts

- Complete repair and effective repair rates
- $\Delta$BPR and saturation across iterations
- Regression, abstention, patch rejection
- Failure classes blocking further progress

## Data policy

Do not import frozen campaigns from prior papers unless the empirical design explicitly requires it and provenance is documented.

Implementation and frozen exports will be versioned in public releases after campaigns complete.
