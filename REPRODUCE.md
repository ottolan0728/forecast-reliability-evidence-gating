# Reproduce the public derived-output audit

## Status and limits

Release recommendation: **REVISE**. Six accepted-supplement AUPRC cells remain inconsistent with the frozen results; see docs/ACCEPTED_NUMERICAL_DISCREPANCIES.md. A passing software smoke test is not a passing scientific-publication consistency gate.

This package preserves exact frozen numeric outputs. It supports table reconstruction from frozen entity-level statistics and seven original diagnostic plot blocks without reading source observations, fitting models, or rerunning experiments. Do not describe that limited command as an end-to-end raw-data reproduction of the paper.

## Clean environment and one smoke command

Install uv, then from the repository root:

```sh
uv venv .venv --python 3.11.13
uv pip install --python .venv/Scripts/python.exe -r environment/release-audit-requirements.txt
uv run --no-project --python .venv/Scripts/python.exe python scripts/public_smoke.py --output ../public-smoke-new
```

On Linux/macOS replace `.venv/Scripts/python.exe` with `.venv/bin/python`. The output directory must be new and outside the repository. The command checks file hashes, scans public text, parses frozen code without executing it, rebuilds existing macro tables, verifies the 40/40 and 39/40 descriptive counts, and regenerates seven figures from exact frozen plotting statements. Counts are exact; reconstructed floating summaries use absolute tolerance 1e-12 and rtol=0.

Use `--require-publication-ready` to make the command exit with code 2 while the printed-cell discrepancy remains. That flag is a publication guard, not a request to change scientific results. The stored 146,964-check verification is historical; this release smoke test does not rerun those row-level checks.

Standalone plotting command:

```sh
uv run --no-project --python .venv/Scripts/python.exe python scripts/regenerate_frozen_figures.py --output ../frozen-plots-new
```

## Code and data boundary

`src/frozen/primary/`, `src/frozen/r9/`, and `src/frozen/r1/` preserve the actual scientific algorithms. Private default paths were redacted, not numerical settings. These are archival reference sources, not drop-in entry points: they retain historical directory contracts and inventory/hash guards. **Do not bypass their guards or execute their fitting functions as part of this release.**

Obtain BDG2 and CKW separately as described in DATA.md. Place local inputs under gitignored `data/raw/bdg2/` and `data/raw/ckw/`. Raw data and hourly tapes containing true or lagged loads are deliberately absent. A portable raw-data-to-frozen-tape reconstruction path is not yet supplied or validated. The original private-path inventory cannot safely be committed, and merely placing raw data in those folders does not make the archival scripts executable. This is an explicit remaining v1.0.0 requirement.

Frozen diagnostic plotting code is included. Some accepted editorial re-layouts have only PDFs in the available accepted archive; these are preserved without inventing replacement source code. Figure aliases map identical archived and accepted PDFs. Exact figure bytes may depend on PDF timestamps, fonts, and backend versions; numeric inputs and plotting statements are the reproducible targets.

## Evidence tiers

Original q95/7-day primary comparisons remain primary. R9 and R1 completed diagnostics are post-outcome secondary. Feasibility artifacts are not architecture validation; the new-cohort extension remains unresolved. Within mixed tables, CKW lag-168 and robustness settings other than q95/7-day remain secondary. See LINEAGE.md and configs/PLAN_LOCK.md. No entity, configuration, or unfavorable result was removed from the included scientific tables.
