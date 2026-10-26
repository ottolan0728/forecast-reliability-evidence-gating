# CKW historical snapshot limitation

## Scope

This note documents a reproducibility limitation affecting the exact byte-level reconstruction of the CKW raw-input snapshots used for the accepted Energy & Buildings article.

## Current status

The accepted analysis used frozen CKW monthly source files whose identities were recorded before analysis. During public-release preparation, the current CKW Open Data endpoint was checked again.

CKW states that the aggregated smart-meter datasets are updated at the beginning of each month and that the provider may change or discontinue the Open Data offering. The current endpoint serves current exports for the relevant months, but the public-release audit cannot certify those current files as byte-identical to the historical 2025-09 through 2025-12 snapshots used by the frozen analysis.

Accordingly:

- the exact historical raw CKW snapshots are **not redistributed** in this repository;
- current CKW files must **not** be substituted silently for the frozen historical inputs;
- the public package preserves frozen derived inputs, deterministic evaluation code, source hashes, lineage records, and verification artifacts;
- derived/frozen result reconstruction remains available;
- exact raw-source-to-frozen-evaluation reconstruction for those historical CKW months remains provider-dependent.

## Scientific impact

This limitation does not change the accepted manuscript, frozen scientific results, or the six Supplementary Table S6 production corrections. The public-release audit independently reconstructed the available frozen components and retained the original evidence boundaries.

## Release interpretation

A future versioned release may document this as a provider-side historical-snapshot limitation rather than claiming byte-identical reconstruction from the provider's current endpoint. No current CKW export should be represented as the original frozen source unless its identity is independently verified.
