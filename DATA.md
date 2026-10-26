# Data availability and provenance

## Building Data Genome 2

The reserved-site evaluation uses electricity-meter data from the **Building Data Genome Project 2 (BDG2)**:

Miller, C. et al. *The Building Data Genome Project 2, energy meter data from the ASHRAE Great Energy Predictor III competition.* Scientific Data 7, 368 (2020).

The accepted study evaluates 20 reserved buildings from five sites; 17 buildings support the predefined peak comparison.

## CKW

The separate-family evaluation uses aggregated smart-meter consumption data from the **CKW open-data portal**. The accepted evaluation contains 116 postal areas in one service territory.

The study constructs hourly targets from four valid 15-minute observations. Missing, invalid, or negative quarter-hour observations invalidate the corresponding hour; zero consumption remains valid. Missing values are not interpolated.

## Redistribution policy

Raw BDG2 and CKW source data are not redistributed here. Users should obtain the data from the original repositories and comply with the corresponding source terms and licenses.

This repository will contain only derived or non-restricted artifacts needed to reproduce the reported analysis, together with data-retrieval and preprocessing notes where appropriate.

## Temporal roles used in the accepted paper

- January–June: point-model fitting
- July: residual-scale and comparative-gain auxiliary models
- August: calibration and admission-threshold freezing
- September: update history
- October–December: held evaluation window

These roles are frozen before evaluation in the accepted study.

## Exact source contract and reconstruction

`configs/RAW_INPUT_CONTRACT.json` locks 13 inputs by size and SHA-256, the 20-building and 116-area frozen registries, temporal roles and feature extraction identity. The BDG2 electricity file is pinned to commit d08f5d010392979e5c24a4c18967d5014c495709 and Git LFS SHA-256 039d909d8981e2d69eaeb366144e6ab7e84fa5e7e216aee42bddd95384a66418. The contract gives its immutable media URL.

CKW uses 12 original 2025 monthly Dataset B files. **Public acquisition is blocked for September–December:** current official URLs return different compressed and uncompressed CSV bytes. Required historical hashes and observed current hashes are recorded; no newer source may be substituted. Obtain hash-matching historical versions from the provider or an authorized original copy. We do not redistribute raw files.

Input layout is an external directory containing `bdg2/electricity.csv` and the exact `ckw/` filenames in the contract. REPRODUCE.md gives complete download, dry-run, validation and reconstruction commands. Outputs contain observations and stay outside the public repository.

Preprocessing preserves the frozen cohort, training q99 normalization and q95 peak thresholds, missing-value/DST rules, lag/history requirements and calendar features. CKW development months retain their original August boundary and CSV serialization interface; September does not backfill August. The accepted fixed point predictions and admission masks are restored from audited label-free components, without refitting. Local full reconstruction is verified; this does not resolve unavailable public historical CKW versions.
