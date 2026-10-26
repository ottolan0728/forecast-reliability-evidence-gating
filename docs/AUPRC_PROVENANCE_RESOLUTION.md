# AUPRC provenance resolution

All six CKW Table S6 cells are ACCEPTED_SUPPLEMENT_PRESENTATION_TRANSCRIPTION_ERROR. The precise authoring cause is not established. The earliest located source is the hardcoded R1 DEVELOPMENT V01 supplement, propagated through later candidate sources and the accepted supplement. No legitimate frozen numerical source was found for the six printed values.

The search inspected 417 source/archive entries, with 220 hits or byte-identical duplicates and 12 unique frozen configuration/aggregation rows. The complete search inventory and hits, source hashes, frozen versions, six pooled recomputations and 696 entity checks are in verification/resolution. Scope includes R1, frozen bundle, original E1/C1 and R9 sources, scripts, available logs, intermediate tables and archived supplement candidates; absence is limited to those available artifacts.

Accepted E2 definition: positive = (absolute point error minus absolute fallback error) / frozen scale > 0; score = gain_score; retain rows with observed y. Pool across 116 entities separately for each model/fallback configuration (256012 rows per configuration). AUPRC is non-interpolated average precision, sum of recall increments times precision at tied-score group ends. It is not trapezoidal PR area or entity-macro AP.

An independent tied-score implementation and sklearn average_precision_score agree with the frozen configuration metrics within 1.6653345369377348e-16. All 696 tape hashes match frozen input manifests. No model fitting occurred. Prespecified provenance checks for entity-macro aggregation, non-strict positive class, harmful class with reversed score, residual-risk score and trapezoidal area do not explain the printed values. These checks were not a formula search to fit the publication.

| Configuration | Accepted S6 | Corrected production candidate |
|---|---:|---:|
| HGB lag-1 | 0.459 | 0.398 |
| HGB lag-24 | 0.510 | 0.405 |
| HGB lag-168 | 0.444 | 0.371 |
| Ridge lag-1 | 0.616 | 0.496 |
| Ridge lag-24 | 0.626 | 0.530 |
| Ridge lag-168 | 0.539 | 0.448 |

Each row has the same error classification. Exact unrounded values and hashes are in AUPRC_RECOMPUTATION.csv and AUPRC_TAPE_MANIFEST.csv. Original accepted checks are retained separately. The production correction is prepared, not submitted. No model, analysis, primary result, conclusion or inferential claim changes.

The local corrected PDF uses six exact PDF text-token replacements, not LaTeX recompilation. Twelve-page pixel comparison found changes only within the six cells, with zero changed pixels outside. Original and corrected PDF/source hashes are preserved in CORRECTION_HASHES.json. Full accepted and corrected manuscript assets remain outside the public code payload; the public package contains the six-cell source excerpt and audit evidence.

The full local provenance inventory retains private-source filenames. Public inventory/hit rows retain hashes but withhold correspondence-related filenames. Source archive path aliases denote frozen artifacts, not downloadable public documents.
