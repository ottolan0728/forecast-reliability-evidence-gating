# Forecast Reliability Evidence Gating

Reproducibility repository for the accepted **Energy & Buildings** manuscript:

> **Auditing Forecast Replacement in Building and Aggregated Electricity Loads: Reliability, Fallback Utility, and Peak Outcomes**

**Manuscript:** ENB-D-26-08510R1  
**Journal:** Energy & Buildings  
**Status:** Accepted for publication (26 October 2026)

## Overview

This repository supports the evidence-gating study of forecast replacement decisions in short-term electricity-load forecasting. The study separates three claims that are often conflated:

1. **screening reliability** — evidence that an issued forecast may be unreliable;
2. **replacement utility** — evidence that the numerical fallback actually improves delivered forecast loss; and
3. **peak protection** — evidence that replacement improves performance on a peak-restricted population.

The repository is intended to preserve the analysis logic, deterministic evaluation utilities, figure-generation workflow, derived result tables, and non-restricted reproducibility artifacts used for the accepted paper.

## Main study components

- Building Data Genome 2 (BDG2) reserved-site evaluation
- CKW aggregated smart-meter evaluation
- Evidence-Gated Forecast Replacement and Audit (EGFRA)
- Calibrated Comparative-Gain Admission (CCGA)
- frozen primary analyses
- post-outcome secondary diagnostics:
  - exact matched replacement-rate comparisons
  - comparative-gain reliability diagnostics
  - fixed-mask fallback sensitivity
  - one-factor-at-a-time CCGA sensitivity
  - extended metrics and computational diagnostics
  - month-specific stability summaries
  - peak-alert diagnostics

## Data

Raw source datasets are **not redistributed** in this repository.

- **BDG2:** Building Data Genome Project 2, Miller et al., *Scientific Data* 7, 368 (2020).
- **CKW:** aggregated smart-meter consumption data from the CKW open-data portal.

See [DATA.md](DATA.md) for provenance and reconstruction notes.

## Reproducibility

The accepted manuscript reports a final numerical verification pass of **146,964 checks with zero failures**. Frozen primary analyses and opened-cohort secondary diagnostics remain explicitly separated.

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the evidence-status rules and repository organization.

## Availability status

The frozen public payload has been extracted and audited. **v1.0.0 recommendation: REVISE** because six accepted-supplement AUPRC cells do not match the frozen artifacts, and full raw-input reconstruction/editorial figure-source coverage remains incomplete. No scientific outputs were changed. See [public release audit](docs/PUBLIC_RELEASE_AUDIT.md), [file register](docs/PUBLIC_FILE_REGISTER.csv), and [executable smoke instructions](REPRODUCE.md). Raw data remain governed by their original sources and licenses. No DOI or release tag has been created.

## Citation

Citation metadata are provided in [CITATION.cff](CITATION.cff). The final DOI and bibliographic details will be added after Elsevier production assigns them.

## Authors

- Chun-Jan Tseng — Soochow University
- Yi-Kai Su — National Defense University
- Ming-Han Chang — National Yang Ming Chiao Tung University

## Repository note

This repository is for scientific reproducibility and evidence traceability. Post-outcome diagnostics are retained as secondary analyses and must not be reinterpreted as a fresh confirmatory family.
