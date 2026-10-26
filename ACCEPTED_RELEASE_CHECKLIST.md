# Accepted-paper public release checklist

Article accepted by **Energy & Buildings** on **26 October 2026**.

## Completed

- [x] Public repository created
- [x] README with accepted-paper scope
- [x] Data provenance and no-redistribution policy
- [x] Reproducibility/evidence-status contract
- [x] Citation metadata placeholder
- [x] Public release manifest
- [x] Git ignore rules for raw/private material
- [x] Internal-to-reader-facing lineage map
- [x] Final numerical verification summary
- [x] Accepted R1 derived-result readout

## Pending before v1.0.0 archival release

- [x] Public analysis code copied from the frozen accepted-paper archive
- [x] Deterministic evaluation utilities copied from the frozen archive
- [ ] Figure-generation code copied from the frozen archive
- [x] Environment/dependency specification copied from the frozen archive
- [x] Complete public derived CSV tables copied from the frozen archive
- [x] Non-restricted prediction/diagnostic artifacts reviewed and copied
- [ ] One clean end-to-end reproduction command documented
- [ ] Repository smoke test from a clean environment
- [ ] Final article DOI and bibliographic metadata added after production
- [ ] GitHub v1.0.0 release created
- [ ] Zenodo archival DOI minted and cross-linked

No raw BDG2 or CKW source data, private reviewer correspondence, or redistribution-uncertain artifacts should be added.

## Release audit status

**REVISE**: six Supplementary Table S6 AUPRC cells remain unreconciled. Frozen CSVs are retained unchanged. The derived-output smoke test is documented in verification/SMOKE_TEST_REPORT.md; full raw-data end-to-end reconstruction and all accepted editorial figure sources are not yet complete. Raw/prediction tapes containing source observations were reviewed and excluded, not copied. Figure utilities cover seven frozen diagnostics and recovered primary diagram sources, not every editorial re-layout. No tag, Zenodo DOI, manuscript edit or new scientific analysis was made.
