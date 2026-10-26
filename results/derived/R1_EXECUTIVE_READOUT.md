# R1 executive readout

## Frozen-primary verification

G0 PASS: **34,002 frozen-primary checks** (maximum loss difference 2.1094237467877974e-15), plus **552 R9 checks**, at tolerance 1e-12 with exact counts. Frozen primary results were unchanged.

## Feasibility boundaries

- **Fresh cohort:** no untouched status was certified for the remaining 1,578 inventoried BDG2 electricity entities. No independent-site expansion is claimed.
- **Architecture diversity:** the full-cohort LSTM/TCN feasibility program failed the inherited August complete-window support rule for one reserved entity (192 available rows versus 336 required). A six-entity, 12-fit smoke test passed, but partial fits are not presented as architecture validation.

## Matched-rate diagnostic

Comparative-gain ranking has lower entity-macro average replacement effect than residual-risk ranking in **40/40 matched cells** and lower peak-restricted effect in **39/40 cells**.

These are descriptive post-outcome comparisons, not independent successes, a globally adjusted confirmatory family, or evidence that replacement necessarily improves versus keeping the original forecast.

## Gain-estimator diagnostics

| dataset | model | lag | Spearman | AUROC | harmful-positive rate | frozen-switch harm rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| E1 | HGB | 24 | 0.543304864 | 0.719258505 | 0.393281132 | 0.336133277 |
| E1 | Ridge | 24 | 0.490313786 | 0.709493955 | 0.364050633 | 0.326330532 |
| C1 | HGB | 1 | 0.484230394 | 0.634345348 | 0.566276724 | 0.548857560 |
| C1 | HGB | 168 | 0.450785951 | 0.640024593 | 0.603105246 | 0.613437196 |
| C1 | HGB | 24 | 0.355860537 | 0.602303138 | 0.580077354 | 0.586910286 |
| C1 | Ridge | 1 | 0.338682262 | 0.617426866 | 0.468729633 | 0.456532638 |
| C1 | Ridge | 168 | 0.285564235 | 0.611502973 | 0.536022224 | 0.529334626 |
| C1 | Ridge | 24 | 0.199134305 | 0.584537077 | 0.462771349 | 0.451135638 |

Positive gain scores are therefore not interpreted as safety certificates.

## Fixed-mask fallback sensitivity

Selected entity-macro examples from the frozen admitted masks:

| dataset | model | original lag | delivered fallback | delta average | delta peak | switch rate |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| C1 | Ridge | 24 | lag24 | -0.000918472621 | -0.000423275624 | 0.330580803 |
| C1 | Ridge | 24 | learned_HGB | -0.004244625230 | -0.003660457440 | 0.330580803 |
| E1 | HGB | 24 | lag24 | -0.010984094300 | 0.000623498006 | 0.168777709 |
| E1 | HGB | 24 | learned_Ridge | -0.010111058600 | -0.0000887471263 | 0.168777709 |
| E1 | Ridge | 24 | lag24 | -0.002269989610 | 0.002582605250 | 0.217045367 |
| E1 | Ridge | 24 | learned_HGB | 0.007726626930 | -0.001317708940 | 0.217045367 |

These are counterfactual fixed-mask sensitivities. They do not establish that the original routing mask is optimal for the alternative fallback.

## Peak-alert proxy

Admitted-policy entity-macro changes:

| dataset | model | lag | change recall | change false-alarm rate | change F1 |
| --- | --- | ---: | ---: | ---: | ---: |
| C1 | HGB | 1 | -0.000329806688 | 0.00000406948617 | -0.000217911189 |
| C1 | HGB | 24 | -0.003928650240 | -0.000222671481 | -0.001134952380 |
| C1 | HGB | 168 | -0.001608535590 | -0.0000329368484 | -0.000850696427 |
| C1 | Ridge | 1 | 0.007947548320 | 0.000732468265 | 0.001704093140 |
| C1 | Ridge | 24 | 0.016653879900 | 0.001510533600 | 0.002206245200 |
| C1 | Ridge | 168 | -0.013185429700 | 0.001401028980 | -0.021318208400 |
| E1 | HGB | 24 | -0.015944036400 | -0.003596622970 | 0.000412608967 |
| E1 | Ridge | 24 | -0.021785489000 | -0.001404239070 | -0.006361699660 |

The alert proxy is descriptive and is not interpreted as demand-charge savings, capacity protection, battery value, demand-response benefit, or another physical/economic grid outcome.

## Selection discipline

No post-outcome best budget, threshold, calibration window, fallback, or entity subset replaces the frozen primary design. Representative timing evidence is an engineering benchmark, not a fleet-level runtime guarantee.
