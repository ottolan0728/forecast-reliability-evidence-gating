# Accepted supplement / frozen artifact discrepancy

Status: UNRESOLVED. Do not tag v1.0.0. Neither manuscript nor frozen scientific values were edited.

The six CKW AUPRC cells in Supplementary Table S6 disagree with the frozen pooled configuration metrics. The entity-macro AUPRC values also do not explain these printed values. This audit has not established the cause.

| Configuration | Printed S6 | Frozen pooled AUPRC |
|---|---:|---:|
| HGB, lag-1 | 0.459 | 0.39774556777837006 |
| HGB, lag-24 | 0.510 | 0.40533889506702114 |
| HGB, lag-168 | 0.444 | 0.3708170329067485 |
| Ridge, lag-1 | 0.616 | 0.49591204911342096 |
| Ridge, lag-24 | 0.626 | 0.53017560445223455 |
| Ridge, lag-168 | 0.539 | 0.44830614927820828 |

Source: results/derived/E2_gain_diagnostics/configuration_metrics.csv, aggregation=pooled_descriptive. Supplement identity is recorded in docs/SOURCE_PROVENANCE.json. The compared supplement PDF is byte-identical to the frozen final-candidate supplement. The 246 printed-cell comparisons have 240 passes and these six failures. This includes 22 readout entries formatted from nine significant digits and padded with zeros; their original exact-display mismatch is retained in the check table, and the underlying CSV cells are unchanged.

Resolution requires the Research Lead to reconcile accepted presentation and frozen evidence; no new model, retuning or selective deletion is warranted by this finding.
