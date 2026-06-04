# Feasibility probe — iterative oracle-guided repair

**This is a feasibility probe, not the final EMSE experiment.** No manuscript claims should be drawn from probe outputs until a frozen campaign is designed, executed, and audited.

## Scientific question

Can iterative oracle-guided repair improve behavioural correctness of LLM-generated FSMs that are structurally acceptable but behaviourally incorrect?

## Scope (probe)

| Parameter | Value |
|-----------|--------|
| Model | `qwen2.5-coder:7b` |
| Max iterations | 3 |
| Repair condition | `patch_trace_feedback` (IST repair protocol) |
| Candidates | 10–15 slots from `pilot_repair_cases_diverse` (G2-pass, BPR &lt; 1, qwen only) |
| Infrastructure | Reuses `ist2026b/fsm-repairability-study` scoring, diagnostics, patch application, Ollama patch generation |

## Data sources (read-only)

- **Cases:** `~/papers/ist2026b/paper/experiments/pilot_repair_cases_diverse/`
- **Selection report:** `candidate_selection_report.csv` (links to EMSE C1/C2 candidates)
- **Gold / oracles:** copied per case (`reference_fsm.json`, `oracle_suite.json`)
- **Repair tooling:** `~/papers/ist2026b/fsm-repairability-study/scripts/`

Prior frozen campaigns under `ist2026b/fsm-repairability-study/freezes/` are **not** modified.

## Output layout

Internal mirror: `~/papers/emse2026b/paper/experiments/iterative_repair_probe_001/`

```text
iterative_repair_probe_001/
  manifest.json
  run_config.json
  inventory_report.md
  dry_run_summary.json
  analysis.json
  cases/<case_id>/...
  summary.json
  summary.csv
```

## Scripts

| Script | Role |
|--------|------|
| `scripts/build_feasibility_manifest.py` | Inventory + `manifest.json` |
| `scripts/run_iterative_oracle_repair_probe.py` | Probe runner (`--dry-run` supported) |
| `scripts/analyze_iterative_repair_probe.py` | Aggregates probe metrics |
| `scripts/repair_probe_lib.py` | Shared imports from repair study |

## Environment

```bash
cd ~/papers/emse2026b/fsm-oracle-repair-loops
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r environment/requirements.txt
pip install -r ~/papers/ist2026b/fsm-repairability-study/environment/requirements.txt
```

Set `FSM_REPAIR_REPO` if the repair study is not at the default sibling path.

## Live run (after explicit approval)

Remove `--dry-run` and ensure Ollama serves `qwen2.5-coder:7b`:

```bash
export FSM_REPAIR_REPO=~/papers/ist2026b/fsm-repairability-study
cd ~/papers/emse2026b/fsm-oracle-repair-loops

python3.12 scripts/run_iterative_oracle_repair_probe.py \
  --input-manifest ../paper/experiments/iterative_repair_probe_001/manifest.json \
  --output-dir ../paper/experiments/iterative_repair_probe_001_live \
  --model qwen2.5-coder:7b \
  --max-iterations 3 \
  --temperature 0 \
  --limit 15
```

Use a **new** output directory (e.g. `_live`) so dry-run artefacts remain untouched.

## What not to do yet

- Do not cite probe counts in the manuscript.
- Do not publish to Zenodo.
- Do not overwrite `ist2026b` freezes or EMSE campaign trees.
