# Public release smoke test

PASS for the derived-output software scope; publication recommendation remains **REVISE**.

A fresh Python 3.11.13 environment was created and populated with all 19 exact archived package versions. pypdf 6.10.0 was added only for release PDF auditing. A clean copy containing no Git metadata, raw data, historical runtime environment or external source tree ran the documented command successfully. Source scientific code was syntax-checked but not executed.

The test verifies public file registration and SHA-256, scans text for secrets/private paths, verifies absence of observation columns, reconstructs four existing macro tables to absolute tolerance 1e-12, checks the 40/40 and 39/40 descriptive comparisons, and executes seven exact frozen diagnostic plotting blocks using only archived summaries. It does not retrain, tune, access hourly observations, or rerun scientific experiments. Historical row-level verification remains a separately labeled archived artifact.

The first clean candidate passed 361 checks. Final-package counts are recorded in SMOKE_TEST_RESULT.json and SMOKE_CHECKS.csv. The first smoke attempt found a scanner false positive on a legitimate HTTPS URL; the drive-path matcher was corrected and the complete clean test rerun. No scientific settings or data changed.

Six Supplementary Table S6 AUPRC cells remain inconsistent with the frozen CSV. The software PASS must not be used to assert publication readiness or complete raw-data reproduction. Use --require-publication-ready to obtain a nonzero exit while this mismatch remains. See ../docs/PUBLIC_RELEASE_AUDIT.md for all remaining release blockers.
