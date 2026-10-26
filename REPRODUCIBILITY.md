# Reproducibility and evidence status

## Scope

This repository supports the accepted Energy & Buildings manuscript ENB-D-26-08510R1.

The study distinguishes between frozen primary analyses and secondary post-outcome diagnostics. Reproduction of numerical outputs does not change the evidential status of an analysis.

## Evidence-status rules

- **Primary analyses:** frozen before evaluation and retained as the confirmatory family.
- **Secondary diagnostics:** specified after primary outcomes were inspected and retained as descriptive or mechanism-level analyses.
- **Feasibility artifacts:** engineering checks that are not presented as scientific validation.
- **Unresolved extensions:** no additional BDG2 cohort was promoted as an untouched external cohort, and full-cohort LSTM/TCN validation was not claimed.

## Verification

The accepted revision records a final numerical verification pass of 146,964 checks with zero failures. These checks verify consistency between archived outputs and reported summaries; they are not described as independent retraining or external replication.

## Intended repository contents

Public materials are organized around:
- analysis and deterministic evaluation utilities;
- figure-generation code;
- configuration and environment records;
- derived result tables;
- non-restricted prediction or diagnostic artifacts;
- provenance and verification notes.

Raw source datasets are not redistributed. See DATA.md.

## Reproduction principle

Users should preserve the accepted manuscript's temporal roles, entity definitions, outcome definitions, and evidence-status boundaries. Post-outcome diagnostics should not be re-labeled as a new confirmatory family.
