# Repository scope

This project maintains two directories with distinct roles.

## Private research workspace (`paper/`)

**Purpose:** Day-to-day research, writing, and exploration for the EMSE manuscript.

**May contain:**

- Manuscript drafts and revision history
- Exploratory scripts and one-off analyses
- Raw experiment logs and incomplete campaigns
- Notes, hypotheses, and discarded approaches
- Temporary figures and internal checklists

**Must not be assumed:** Reproducible, complete, or redistributable.

## Public artifact repository (`fsm-oracle-repair-loops/`)

**Policy alias:** `repo-externo` in project directory policy.

**Purpose:** GitHub and Zenodo deposit for iterative oracle-guided repair studies.

**Must contain only:**

- Final (or paper-reported) datasets and oracle definitions
- Frozen prompts for reported conditions
- JSON schemas and minimal deterministic scripts
- Aggregated results needed to verify claims
- Documentation: study design, terminology, reproducibility, data statement

**Must not contain:**

- Unpublished manuscript sources (default)
- Exploratory campaigns not cited in the paper
- Private absolute paths or credentials
- Material whose primary goal is an open-ended LLM leaderboard

## Scientific boundary

This artifact studies **iterative behavioural recovery** under oracle feedback, building on prior findings that structural validity and single-iteration repair measurement are insufficient to characterize saturation, regression, and blocking failure classes across iteration budgets.

Structural gates may appear as preconditions; the scientific object is **iteration-aware behavioural repair outcomes**.

## Synchronization policy

1. Design and pilot in `paper/`.
2. Freeze iteration campaigns and summaries cited in the paper.
3. Export only the frozen subset into `fsm-oracle-repair-loops/experiments/frozen/`.
4. Tag the public repo and deposit on Zenodo; back-fill DOI in `CITATION.cff`.

## Maintainer checklist (before release)

- [ ] No references to private `paper/` paths in public files
- [ ] `CITATION.cff` and `LICENSE` finalized
- [ ] `REPRODUCIBILITY.md` commands verified on a clean machine
- [ ] Checksums documented for frozen directories
- [ ] Author identity matches canonical metadata
