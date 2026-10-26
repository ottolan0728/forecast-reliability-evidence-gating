# Public release audit — 26 October 2026

**Recommendation: REVISE for GitHub v1.0.0.** This is a release-preparation payload, not a tagged scientific release. No DOI was created. No manuscript was edited, no model was trained, and no new scientific outcomes were generated.

## Evidence and checks

The exact frozen R1 audit archive has SHA-256 `b0f0653284bfe2fe0fcbd6feffc097dc8aeea64eb7a641260ccd5d511ade3129`. Its internal checksum manifest and corresponding local payload were verified before extraction. File-by-file decisions precede candidate copying. Every public payload is registered with source and released hashes. Numerical columns in all included original CSVs were compared exactly against the frozen source: 897 extraction/identity and inventory checks passed. The accepted main and supplement plus existing public readout yielded 246 printed-cell checks: 240 pass, six fail. Full details are retained in verification/.

Six CKW AUPRC cells in Supplementary Table S6 disagree with frozen configuration metrics. Both pooled and entity-macro alternatives were inspected; neither explains the printed values. This is not a rounding discrepancy. See ACCEPTED_NUMERICAL_DISCREPANCIES.md. The audited primary table cells agree. The public readout uses some nine-significant-digit values padded with zeros; that presentation rule is explicitly recorded, without changing any frozen CSV value.

The clean smoke test reconstructs existing summaries and seven frozen diagnostic plots. It does not rerun the historical 146,964 row-level checks or experiments. Its report is verification/SMOKE_TEST_REPORT.md. Historical verification files remain clearly labeled under verification/frozen/.

## Exclusions and redactions

Excluded: raw observations and truth/lagged-load tapes, calibration observation files, checkpoints, caches, duplicate figures/archives, private correspondence/submission exports, report-drafting/citation-triage orchestration, private inventories, and unrelated exposure-history material. Engineering feasibility retains configuration, planned seeds and cohort support counts; partial model fits and prediction tapes are excluded. Unfavorable scientific table rows were not filtered.

Private path strings in scientific source defaults and CSV provenance columns are replaced with public placeholders. Public source paths are root-relative locators (R1_FREEZE, FROZEN_INPUTS, ACCEPTED_SUBMISSION); the full absolute-location register stays offline. This resolves the requirement to retain source lineage without publishing personal filesystem locations. Package versions are retained; interpreter locations and host identifiers are excluded. PDF metadata, extracted text, attachments and public textual payloads were scanned. A literal secret-detection regex is not a credential. Generic revision/evidence labels do not reveal reviewer identity or correspondence.

The register lists every file, including generated release audit utilities. It distinguishes those utilities from frozen scientific code. The register cannot contain its own cryptographic digest; its row explicitly excludes that self-reference, and the Git commit plus external upload manifest bind its bytes. SHA-256 source and destination values are otherwise supplied. Excluded candidate paths may retain internal experiment identifiers solely for lineage; see LINEAGE.md.

## Remaining release blockers

1. Reconcile the six accepted-supplement AUPRC discrepancies with the Research Lead. Do not change frozen outputs to fit the manuscript.
2. Locate exact frozen source for remaining accepted editorial figure re-layouts. Original diagnostic plotting blocks and matching primary diagram sources are included; new replacements must not be called frozen originals.
3. Supply and validate a portable raw-data-to-frozen-evaluation reconstruction path without private paths or redistributed observations. Current archival scripts preserve algorithms and historical guards; the public smoke command verifies derived-table reconstruction only.

No GitHub v1.0.0 tag/release or Zenodo DOI should be created until these items are resolved. The safe filtered preparation payload can be committed independently of that decision.
