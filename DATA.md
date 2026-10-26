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

## Retrieval and local placement

BDG2: use the official repository https://github.com/buds-lab/building-data-genome-project-2 and its raw electricity meter file `data/meters/raw/electricity.csv`; retain original source checksums locally. CKW: follow Aggregate Data at https://www.ckw.ch/landingpages/open-data and obtain the frozen 2025 monthly UTC releases. Do not silently replace a missing historical release with a newer one. Local placement is `data/raw/bdg2/` and `data/raw/ckw/`, both excluded by Git. See REPRODUCE.md for the currently unimplemented portable raw-input reconstruction boundary and docs/RIGHTS_AND_ATTRIBUTION.md for source terms.
