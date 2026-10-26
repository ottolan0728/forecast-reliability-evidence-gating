# Reproduce the frozen public evidence

Recommendation: **REVISE** pending exact public CKW September–December 2025 source availability. The six S6 errors are resolved as presentation/transcription errors; a corrected production candidate is prepared but not submitted. Original accepted and candidate checks remain separate. See docs/AUPRC_PROVENANCE_RESOLUTION.md and docs/CKW_SOURCE_IDENTITY_BLOCKER.md.

## Clean environment

```sh
uv venv .venv --python 3.11.13
uv pip install --python .venv/Scripts/python.exe -r environment/release-audit-requirements.txt
uv run --no-project --python .venv/Scripts/python.exe python scripts/public_smoke.py --output ../public-smoke-new
```

On Linux/macOS use `.venv/bin/python`. Outputs must be new directories outside the repository. Smoke verification checks the file register, privacy and syntax, reconstructs four frozen macro summaries and executes seven plotting blocks. No model fitting occurs. `--require-publication-ready` exits 2 while the CKW availability gate remains blocked. Historical 146964-check verification is preserved, not claimed as rerun by this command.

## Exact raw-input reconstruction, without fitting

Obtain original sources separately; DATA.md and configs/RAW_INPUT_CONTRACT.json specify every filename, size, SHA-256 and frozen role. Set the example `../private-inputs` to your input directory outside the repository. BDG2 has a verified immutable source. CKW September–December current public files have changed and automatic acquisition is refused; supply only separately obtained matching historical bytes.

```sh
uv run --no-project --python .venv/Scripts/python.exe python scripts/reconstruct_inputs.py --input-root ../private-inputs --dataset bdg2 --download --dry-run
uv run --no-project --python .venv/Scripts/python.exe python scripts/reconstruct_inputs.py --input-root ../private-inputs --dry-run
uv run --no-project --python .venv/Scripts/python.exe python scripts/reconstruct_inputs.py --input-root ../private-inputs --validate-only
uv run --no-project --python .venv/Scripts/python.exe python scripts/reconstruct_inputs.py --input-root ../private-inputs --output ../reconstructed-new
uv run --no-project --python .venv/Scripts/python.exe python scripts/verify_reconstructed_evidence.py --reconstruction ../reconstructed-new
```

Dry-run validates all selected source bytes and frozen feature/registry hashes. Validate-only performs preprocessing and frozen training-summary checks without writing observations. Full reconstruction creates hourly series, causal feature tables, temporal-role/peak fields, evaluation tapes and August calibration tapes outside the repository. Those outputs contain observations: keep them private and do not upload them.

The label-free frozen components contain predictions, risk/gain scores, intervals and masks, never observations or persistence values. Reconstruction joins them with exact separately obtained observations. It does not fit, infer, recalibrate, select thresholds or optimize anything. All 1433 restored tapes match the original frozen fields (14879 column checks, max difference 0); all 736 configuration-policy families pass 44648 numerical checks, tolerance 1e-12. This is accepted frozen-evidence reconstruction, not a claim of retraining reproduction. Source-trained artifacts remain archival reference code; do not bypass their historical guards.

## Figures and evidence tiers

`python scripts/regenerate_frozen_figures.py --output ../plots-new` reproduces scientific plot logic through extracted plotting statements and portable I/O. These new PDFs are RECREATED_SOURCE_ONLY. Accepted static layouts and certified paired TeX sources are separately mapped in docs/FIGURE_ALIASES.csv; no recreated PDF is called an accepted original.

Original q95/7-day admitted-policy analyses remain primary. Opened-cohort R9/R1 diagnostics, lag-168 and alternative robustness settings remain secondary. Engineering feasibility and unresolved extensions are separate. LINEAGE.md governs identifiers. No entity, threshold, unfavorable configuration or scientific output was changed.
