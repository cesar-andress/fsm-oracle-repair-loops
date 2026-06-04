# Data dictionary (draft)

Field definitions will be finalized with JSON schemas in `schemas/`. v0.1.0 lists intended entities only.

## Run-level (`repair_run` — planned)

| Field | Description |
|-------|-------------|
| `case_id` | Repair case identifier |
| `run_id` | Unique run instance |
| `iteration_index` | Zero-based iteration within budget |
| `iteration_budget` | Configured maximum iterations |
| `bpr` | Behavioural pass rate on scored stratum |
| `terminal` | Outcome class at slot end |

## Campaign summaries (`results/summaries/` — planned)

| Artifact | Description |
|----------|-------------|
| `iteration_recovery_summary.json` | Rates and \Delta BPR{} by iteration budget |
| `saturation_summary.json` | Marginal gain after 1 vs 3 vs 5 iterations |
| `blocking_failure_summary.json` | Failure classes halting loops |

## Frozen data (`data/frozen/`)

Directory-per-campaign exports with manifest checksums at release time.

No files are defined in v0.1.0.
