# Reproducibility — v1.0.0

All commands assume the repository root `fsm-oracle-repair-loops/`.

## 1. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r environment/requirements.txt
```

**Dependencies:** `matplotlib` only (no pandas).

## 2. Verify checksums

```bash
python3 scripts/verify_freeze.py
```

**Expected:** `OK: 25 file(s) verified under data/frozen_iterative_repair_001`

**Requires:** Python 3.8+ (for `matplotlib`); use `python3` on PATH or an explicit 3.11+ interpreter.

## 3. Print aggregate summary

```bash
python3 scripts/summarize_freeze.py
```

**Expected highlights:**

- Effective repair: qwen7b=3, qwen14b=5, qwen32b=9, others=0
- Complete repair: 0 for all models
- Cross-model: 17/45 improved by ≥1 model; 28/45 by none

## 4. Regenerate tables

```bash
python3 scripts/generate_paper_tables.py
```

**Outputs:**

- `tables/table_model_summary.tex`
- `tables/table_cross_model_repairability.tex`
- `tables/table_failure_taxonomy_by_model.tex`
- `tables/table_system_specific_gains.tex`

## 5. Regenerate figures

```bash
python3 scripts/generate_paper_figures.py
```

**Outputs:**

- `figures/fig_effective_repairs_by_model.pdf`
- `figures/fig_failure_taxonomy_by_model.pdf`

## 6. Compare with shipped files (optional)

```bash
git diff tables/ figures/
```

After a clean run from an unmodified freeze, regenerated files should match the committed v1.0.0 copies (minor PDF binary drift from matplotlib is possible; re-verify numerics via `summarize_freeze.py`).

## Data not required for Tier A

- Internal paths listed in `data/frozen_iterative_repair_001/SOURCES.json`
- Manuscript sources under `../paper/` (private companion tree)
