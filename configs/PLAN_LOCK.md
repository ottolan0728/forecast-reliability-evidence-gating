# R1 PLAN LOCK

Locked 2026-10-13 after G0 PASS and before new R1 evaluation. Sole executor Codex; sequential single writer. Submitted V10 and original R9 immutable. Counts exact and replay numeric tolerance 1e-12. All E1/C1 new outcomes are R1_REVIEWER_TRIGGERED_SECONDARY; original q95/7-day primary remains unchanged. No outcome tuning, entity deletion, favorable-cell selection, or architecture substitution.

Implementation decisions locked prospectively:
- E0X: header/identity inventory only until exposure provenance proves untouched. Unknown exposure is not evidence of non-exposure. No new cohort when exposure history incomplete.
- E1: Python round (ties-to-even), descending score, ascending timestamp, stable original row ordinal. Store every selected ordinal as compressed row table. Naive/CCGA overlays use the same scoreable denominator. Equal-entity descriptive effects plus equal-site E1 inference, synchronous 7-day C1 2000 draws. Ordinary 95% intervals only; no global family-wise claim. Seed 20260920 preserves archived resampling.
- E2: positives strictly >0; harmful strictly <0; zero gains are nonpositive but not harmful. Undefined metrics are NA. Pooled configuration deciles use qcut(10, duplicates=drop); macro summaries average defined entity metrics. Harmful-case loss means normalized delivered fallback absolute loss; also report negative realized gain magnitude. Actual switches include separate naive, admitted, risk masks.
- E3: daily calibration mean is mean of realized normalized gain times candidate mask over all scoreable rows of each calibration day (same frozen statistic), averaged over chronological calendar days. Bootstrap 1000 circular 7-day draws, 5th/95th percentiles, original seed 20260920. OFAT baseline + A fixed0 + B max mean + C support24/7 + D support96/21 + E first14/21/full31. Ties favor larger threshold. Full31 aliases baseline but is reported. Existing A3 linked without duplicating threshold-grid experiments.
- E4: all three masks and both learned directions, all existing persistence alternatives and keep, index intersections audited. No optional new statistical fallback.
- E5: normalized loads by Jan-Jun q99; only complete 168-hour windows, no imputation; cyclical hour/week calendar appended to LSTM last hidden state or TCN last causal feature. LSTM output dropout .1 (single-layer recurrent dropout inapplicable); TCN one causal Conv/ReLU/dropout per specified channel/dilation. MSE training, nonnegative predictions, deterministic seeds base20261012 plus first8hex SHA256(entity) modulo 1000000, identical across architectures. CPU deterministic threads1 unless supported GPU deterministic environment proven. Auxiliary HGB recipe and admission/interval logic copied frozen design. Smoke entities lexicographically first2 E1 and first4 C1, all20epochs, no evaluation scientific outcomes before feasibility decision. Missing required dependency or unrecoverable source history yields documented feasibility failure, not substituted model.
- E6: all frozen policies; native-scale metrics remain perentity. Entity macro only normalized metrics. Engineering representatives lexicographically first entity each dataset/backbone; warmup1 + repeated3 unless memory/runtime prevents, report actual limitations. Timings are measured only, never inferred from walltime of unrelated pipeline. Missing historic timing remains unavailable. No scientific tape replacement.
- E7: calendar October/November/December, no monthly retuning, descriptive.
- E8: strictly forecast>train q95 and truth>q95, NA undefined denominator, FPR=FP/(FP+TN), no grid/economic interpretation.

Exact handoff experiment definitions follow without alteration:
# R1 Reviewer-Triggered Experiment Plan

## Overview

All new E1/C1 analyses below are `R1_REVIEWER_TRIGGERED_SECONDARY`. They answer reviewer questions; they do not replace the submitted primary analysis.

### Priority order

**Tier 0 — mandatory gate**: R1-G0 replay/inventory  
**Tier 1 — highest scientific value**: E0X, E1, E2, E3  
**Tier 2 — reviewer breadth**: E4, E5, E6  
**Tier 3 — bounded operational/temporal interpretation**: E7, E8

Do not skip a Tier 1 item to spend time on a broader Tier 3 embellishment.

---

## R1-G0 — Frozen evidence replay and inventory

Before new analysis:

1. Locate the exact V10 submission source, R9 audit package, frozen E1/C1 tapes, model bytes, thresholds, masks, scripts, environment and manifests.
2. Compute path/size/SHA-256 manifest.
3. Reproduce V10 primary summaries and R9 A1/A2/A3/A5/R9-R from frozen artifacts.
4. Exact counts must match. Numeric summaries: absolute tolerance `<=1e-10` unless the archive specifies stricter stored-precision comparison.
5. If replay fails: STOP all R1 experiments and write `R1_G0_REPLAY_FAILURE.md`.

---

## R1-E0X — Untouched additional BDG2 cohort feasibility and, only if valid, execution

### Reviewer concern
Limited independent-site power and external generalizability.

### Phase A: feasibility only
Inventory BDG2 sites/buildings not used in development, E1, or previous outcome-inspected analyses.

Eligibility may use only:

- site/building identity and metadata;
- meter type / target availability;
- Jan–Sep history availability needed by the frozen recipe;
- deterministic missingness/coverage rules defined before Oct–Dec outcomes are accessed.

Do **not** inspect Oct–Dec forecast errors before locking the cohort.

### Gate
If an untouched cohort cannot be proven, output `E0X_NOT_FEASIBLE.md` and stop this work package only.

If feasible:

- write inclusion/exclusion rule and exact entity list to `PLAN_LOCK.md` first;
- include all eligible entities unless a deterministic cap is predeclared;
- apply the same frozen temporal roles and original primary q95 definition;
- no R1 tuning using this cohort;
- label results `R1_NEW_COHORT`.

Primary output: cohort inventory, avg/peak replacement effects, service denominators, and same inferential unit appropriate to site structure.

---

## R1-E1 — Exact replacement-rate–loss curves

### Reviewer concern
CCGA, naive gain, and residual-risk policies switch at different rates, obscuring information value.

### Purpose
Compare routing **ranking information** at exactly comparable retrospective evaluation replacement fractions, without using target truth to select rows.

### Score families
- Residual-risk score: frozen predicted residual scale, larger = more replacement-prone.
- Comparative-gain score: frozen predicted comparative gain, larger = more replacement-prone.

### Replacement fractions
Use exactly: `{0.05, 0.10, 0.20, 0.30, 0.40}`.

Within each entity/configuration and each fraction `q`:

1. restrict to scoreable issued evaluation rows;
2. rank by the frozen issue-time score only;
3. select exactly `k = round(q*n)` rows;
4. deterministic ties: timestamp ascending, then stable row id;
5. deliver the same prespecified fallback used by that configuration;
6. compute switch fraction, average replacement effect, peak replacement effect.

### Critical label
This is a **retrospective fixed-rate ranking diagnostic**, not a deployable issue-time policy, because the full evaluation-period score distribution is used to impose exact rates. It uses no evaluation target truth for ranking.

### Inference
Use the same inferential unit as the original dataset where technically coherent:

- E1: equal-site contrasts / exact sign-flip logic;
- C1: synchronous 7-day block resampling.

No new global family-wise claim is authorized. Report point estimates and intervals; multiplicity treatment must be explicit.

### Presentation
For each model/fallback:

- x-axis = exact replacement fraction;
- y-axis = average or peak replacement effect;
- curves = residual-risk vs comparative-gain ranking;
- overlay observed frozen naive-gain and frozen CCGA operating points without forcing them to a common rate.

This directly shows whether the gain score ranks useful replacements better at a matched action budget and where admission places the operating point.

---

## R1-E2 — Comparative-gain estimator reliability and error anatomy

### Reviewer concern
The manuscript does not sufficiently characterize whether estimated comparative gains are accurate, stable, or safely aligned with realized gains.

### Use
Frozen out-of-sample Oct–Dec predictions and realized gains. No refitting/tuning.

### Required metrics by dataset/model/fallback
Report both pooled descriptive and entity-macro summaries where defined:

- Spearman rank correlation: predicted vs realized gain;
- Kendall tau (optional but recommended);
- AUROC for `realized_gain > 0` using predicted gain as score;
- AUPRC for `realized_gain > 0`;
- sign accuracy at predicted gain `> 0`;
- balanced accuracy at predicted gain `> 0`;
- positive predictive value / harmful-positive rate;
- fraction where `predicted_gain > 0` but `realized_gain < 0`;
- mean realized loss in those false-positive/harmful cases;
- same harmful rate among **actual frozen switches** at the frozen threshold.

### Calibration plot
Construct 10 equal-frequency bins of predicted gain (within configuration; if ties prevent 10 bins, use the maximum valid number and report it). For each bin, report:

- n rows;
- mean predicted gain;
- mean realized gain;
- fraction with realized gain > 0.

Also fit descriptive calibration slope/intercept `realized_gain ~ predicted_gain`; no causal interpretation.

### Figures
1. binned predicted-vs-realized gain plot with identity reference;
2. realized-positive fraction by predicted-gain decile;
3. harmful-positive rate by model/fallback.

### No cherry-picking
All frozen model/fallback configurations must appear, even if diagnostics are poor.

---

## R1-E3 — One-factor-at-a-time CCGA component ablation

### Reviewer concern
Incremental contribution of support, threshold search, lower-bound admission, and calibration amount is unclear.

### Baseline
Frozen CCGA exactly as submitted.

### OFAT variants
Do not run a combinatorial factorial. Change one component at a time:

**E3-A — threshold search removed**  
Use fixed `tau=0` while retaining the frozen support requirement and lower-bound admission rule.

**E3-B — lower-bound gate replaced by mean-gain gate**  
Same threshold set and support requirement. Choose the support-qualified threshold with largest calibration mean realized gain; admit only if that mean is >0. Tie-break toward larger threshold.

**E3-C — relaxed support**  
Use minimum 24 selected hours / 7 selected days; otherwise frozen CCGA.

**E3-D — stringent support**  
Use minimum 96 selected hours / 21 selected days; otherwise frozen CCGA.

**E3-E — calibration-length sensitivity**  
Use first 14 days of August, first 21 days of August, and full August, preserving chronology. All other rules frozen. This is a sample-length sensitivity, not a search for the best window.

### Existing evidence
Incorporate pre-submission A3 naive/fixed-threshold/frozen-admitted results rather than redundantly re-inventing them.

### Outputs
For every variant: support counts, chosen threshold/disabled state, test switch share, average/peak replacement effects. Explicitly state that unequal switch rates remain a mechanism-identification limitation where applicable.

---

## R1-E4 — Learned fallback sensitivity under fixed routing masks

### Reviewer concern
Persistence fallbacks may be too weak; replacement utility may be a fallback-quality artifact.

### Required first-line learned fallback
Use the **other already-frozen point backbone** as a learned fallback wherever predictions are aligned and genuinely out-of-sample:

- source Ridge -> fallback HGB;
- source HGB -> fallback Ridge.

Do not select direction based on test performance.

### Fixed-mask design
Reuse frozen masks from residual-risk, naive-gain, and admitted-gain policies. Hold each mask and switch count fixed; change only the delivered fallback.

Compare:

- existing persistence fallbacks;
- learned cross-backbone fallback;
- keep-delivery zero reference.

### Optional statistical fallback
Only if implementation can be prospectively locked before evaluation: a simple seasonal autoregressive/linear fallback trained on Jan–Jun only. Do not add it if specification is ambiguous or would require test-informed tuning.

### Output
Average and peak effects under the same masks, with a figure analogous to A2 but including learned fallback.

---

## R1-E5 — Forecast-architecture diversity stress test

### Reviewer concern
Ridge and HGB are not representative of contemporary temporal architectures.

### Scope lock
Add exactly two representative architectures: **LSTM** and **TCN**. Do not add Transformer/Chronos unless the PI explicitly expands scope after seeing a feasibility report. This is not a model-ranking paper.

### Common task
One-step hourly load forecasting with only issue-time historical load and calendar information. No future weather or unavailable features.

### Input
- lookback: 168 hourly load values;
- cyclic hour-of-day and day-of-week features available at issue time;
- scaling fitted on Jan–Jun only.

### LSTM frozen specification
- one recurrent layer;
- hidden size 32;
- dropout 0.10 where applicable;
- linear output;
- Adam learning rate `1e-3`;
- batch size 64;
- fixed 20 epochs;
- gradient clipping 1.0;
- no hyperparameter search / no early stopping on Oct–Dec.

### TCN frozen specification
- causal 1D TCN;
- channels `[16, 32, 32]`;
- kernel size 3;
- dilations `[1,2,4]`;
- dropout 0.10;
- linear output head;
- Adam learning rate `1e-3`;
- batch size 64;
- fixed 20 epochs;
- no hyperparameter search.

### Training/evaluation roles
- Jan–Jun: point model training;
- July: auxiliary models;
- August: calibration/admission;
- September: update history;
- Oct–Dec: evaluation.

### Fallback and policy scope
Use **lag-24 fallback only** for this architecture-diversity stress test. Evaluate keep, naive gain, frozen-style CCGA, and (if available under the same definition) residual-risk. Do not multiply the experiment by all C1 fallback lags.

### Seeds
Use fixed seed `20261012` plus deterministic entity-derived offsets. Record all seeds.

### Feasibility gate
First run a smoke test on 2 E1 buildings + 4 C1 areas without looking at aggregate scientific outcomes. If code, memory, or time is infeasible, write `E5_FEASIBILITY_FAILURE.md`; do not silently substitute other architectures.

### Interpretation
These are R1 reviewer-triggered architecture stress tests. They do not change the original primary family.

---

## R1-E6 — Extended metrics and computational efficiency

### A. Extended outcomes
For original and routed forecasts, compute where meaningful:

- MAE within entity (native units; never pool raw-scale rows across heterogeneous entities as a universal cross-entity score);
- RMSE within entity;
- normalized RMSE using the same training-scale normalizer `c_i`;
- peak normalized underprediction error: `mean(max(y-g,0)/c_i)` on peak rows;
- maximum normalized absolute error on peak rows;
- fraction of peak rows underpredicted.

Report entity-macro summaries and dataset-specific distributions. Do not present raw pooled MAE across heterogeneous buildings as if scale-invariant.

### B. Computational profile
Separate:

**one-time costs**
- point-model fit;
- residual-scale model fit;
- comparative-gain model fit;
- August calibration / bootstrap admission.

**recurring costs**
- point forecast inference per issued row;
- routing-score inference;
- routing decision + delivered forecast construction;
- daily interval update if applicable.

Measure:

- wall-clock time;
- CPU peak RSS;
- GPU peak allocated memory for LSTM/TCN;
- hardware/software environment.

Use a clearly defined timing harness, warm-up policy, and repeated measurements. Timing reruns are `ENGINEERING_BENCHMARK` and must not replace frozen scientific predictions.

---

## R1-E7 — Evaluation-quarter temporal stability

### Reviewer concern
Single-quarter results may mask temporal instability; full rolling-origin multi-season redesign is not valid post hoc under the frozen study roles.

### Diagnostic
Using the frozen Oct–Dec evaluation only, report October, November, and December separately for:

- switch share;
- average replacement effect;
- peak replacement effect;
- harmful-switch fraction.

No retuning by month. Descriptive first; uncertainty only if technically justified and clearly labeled.

### Manuscript interpretation
This does **not** satisfy full multi-season prospective validation. It characterizes within-quarter stability and supports an explicit limitation/future-work statement.

---

## R1-E8 — Peak-alert operational proxy

### Reviewer concern
Need an illustrative downstream consequence without overclaiming real grid-economic validation.

### Definition
Use the same training-defined q95 threshold `p_i` only as an **empirical high-load alert threshold**.

For original forecast `f` and delivered forecast `g`, define alert if forecast `> p_i` and compare with realized `y>p_i`.

Report:

- peak-alert recall / true-positive rate;
- precision;
- false-negative rate (miss rate);
- false-positive rate;
- F1 score;
- change from original to delivered forecast.

### Boundary
This is an illustrative alert proxy. It is **not** transformer capacity, demand-charge cost, dispatch value, grid security, or policy benefit.

---

## Explicitly not authorized in this round

- broad Transformer/foundation-model benchmark;
- battery dispatch simulation with invented tariffs;
- demand-response optimization with arbitrary costs;
- new peak threshold chosen because it improves results;
- deleting outliers/entities based on test error;
- new random routing baseline unless separately authorized;
- replacing the submitted primary inference family with R1 results.

