# Public reproducibility payload handoff

## Purpose

Populate the public GitHub repository for the accepted Energy & Buildings article:

**Auditing Forecast Replacement in Building and Aggregated Electricity Loads: Reliability, Fallback Utility, and Peak Outcomes**

Manuscript: ENB-D-26-08510R1  
Accepted: 26 October 2026

The repository already contains public documentation, provenance notes, citation metadata, evidence-status rules, lineage mapping, a verification summary, and an R1 derived-result readout.

## Executor

Use **Codex only** for this public-release extraction because Codex executed the study and revision analyses. Do not introduce another executor and do not regenerate scientific results.

## Source freeze

Use the exact frozen artifacts that supported the accepted R1 manuscript. Do not retrain models, rerun experiments to obtain different values, optimize settings, remove entities, or create a new analysis family.

The public release must preserve the accepted distinction between:
- frozen primary analyses;
- post-outcome secondary diagnostics;
- engineering feasibility artifacts;
- unresolved extensions.

## Public allowlist

Copy only artifacts that are necessary and legally appropriate for reproducing the accepted analyses:

1. analysis code and deterministic evaluation utilities actually used for the accepted results;
2. figure-generation code for accepted main/supplementary figures;
3. dependency/environment specifications;
4. frozen configuration files and seeds;
5. public derived result tables used in the accepted paper and supplement;
6. verification scripts and verification summaries;
7. data-retrieval/preprocessing instructions that do not redistribute restricted or uncertain source data;
8. non-restricted prediction/diagnostic artifacts only when redistribution is clearly permitted and necessary.

## Explicit denylist

Do **not** publish:
- raw BDG2 source data;
- raw CKW source data;
- files whose redistribution rights are uncertain;
- reviewer identities, private reviewer correspondence, Editorial Manager exports, or response-drafting history;
- API keys, tokens, credentials, local usernames, absolute personal paths, machine identifiers, or hidden configuration;
- unrelated project artifacts;
- temporary caches, model caches, build outputs, or duplicated files;
- failed scratch experiments unless they are required to explain a published feasibility limitation;
- any artifact that would make a secondary diagnostic look like a fresh confirmatory analysis.

## Reader-facing structure

Prefer this repository layout:

```
src/
scripts/
configs/
environment/
results/derived/
figures/
verification/
docs/
```

Retain internal identifiers only when necessary for lineage. Follow LINEAGE.md:
- E1 = Reserved BDG2 evaluation
- C1 = CKW evaluation

## Required audit before publishing

For every candidate file:
1. record original path;
2. compute SHA-256;
3. classify as INCLUDE / EXCLUDE / REDACT-THEN-INCLUDE;
4. state why;
5. scan for secrets and personal/local paths;
6. check that no raw source data are embedded;
7. check that output values agree with the accepted manuscript and R1_EXECUTIVE_READOUT.md.

Create:
- `docs/PUBLIC_FILE_REGISTER.csv`
- `docs/PUBLIC_RELEASE_AUDIT.md`

## Minimum executable release target

At minimum, a clean user should be able to:
1. install dependencies;
2. place separately obtained BDG2/CKW data according to DATA.md;
3. run deterministic evaluation/reconstruction utilities;
4. regenerate the accepted derived tables and figure inputs that do not require restricted redistribution;
5. run the verification checks.

Document the exact commands in `REPRODUCE.md`.

## Validation gates

Before marking public release complete:
- no scientific result differs from the accepted manuscript;
- primary results remain frozen;
- secondary analyses remain labeled secondary/post-outcome;
- no raw BDG2/CKW data are committed;
- no private review material is committed;
- no credentials or personal absolute paths are committed;
- all public files are listed in PUBLIC_FILE_REGISTER.csv;
- a clean smoke test passes.

## Final deliverables

Commit the filtered public payload to:
`ottolan0728/forecast-reliability-evidence-gating`

Then update:
- README.md
- ACCEPTED_RELEASE_CHECKLIST.md
- CITATION.cff if publication metadata become available

Do **not** create a Zenodo DOI yet unless final publication metadata are available. A GitHub v1.0.0 release may be created after the clean smoke test and public-file audit pass.
