# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 8C-2I Non-Cubicle Cleanup Report

Date: 2026-05-13

Status: dry-run validation passed. Live remains held pending explicit authorization.

## Scope

Phase 8C-2I preserves the successful 8C-2H2 exact-cubicle pre-signal and stabilizer, then adds narrow non-cubicle cleanup for:

- `dynamicBackground/fountain01`: quiet-guard suppression of generic event/foreground and non-cubicle budget-reclaim proposals when no unprotected event-FN risk is present.
- `lowFramerate/tramCrossroad_1fps`: targeted retighten suppression of preserved generic lowFramerate proposals unless strong unprotected event-FN risk exists.

No live, live compare, full CDnet, PTZ-targeted standalone, LASIESTA, SBI2015, BMC, or cross-dataset validation was launched.

## Files

Created configs:

- `configs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2i_dryrun.yaml`
- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_dryrun.yaml`

Created output roots:

- `outputs/asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2i_dryrun/`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_dryrun/`

Updated implementation and compare tooling:

- `src/run_experiment.py`
- `tools/compare_asmag_tr_controller_online_guarded.py`

The default guarded smoke config remains intervention-disabled through `ai_intervention_enabled: false`; 2I behavior is enabled only through separate 2I dry-run configs.

## Commands

```powershell
python -m py_compile src\run_experiment.py tools\compare_asmag_tr_controller_online_guarded.py
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2i_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_smoke_ai_intervention_2i_dryrun
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_dryrun.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_dryrun
```

The targeted mini dry-run was launched only after the smoke dry-run passed.

## Smoke Dry-Run

| Metric | 8C-2I smoke |
|---|---:|
| Jobs | 32/32 completed, 0 failed |
| FMeasure | 0.33797 |
| Event_F1 | 0.58979 |
| Activation | 0.41750 |
| Avg_FPS | 22.00928 |
| P95 latency ms | 445.26664 |
| Proposed intervention rate | 0.33625 |
| Proposed detector request rate | 0.03875 |
| Block-only rate | 0.29750 |
| Event/foreground block-only rate | 0.25375 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |
| Cubicle recall | 0.84848 |
| Cubicle unprotected event FN | 0 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 8 |
| continuousPan proposed intervention rate | 0.04000 |
| tramCrossroad_1fps proposed intervention rate | 0.01000 |
| LowFramerate trim reclaimed proposals | 9 |
| LowFramerate retighten reclaimed proposals | 22 |
| fountain01 quiet-guard reclaimed proposals | 0 |

Smoke dry-run passed all required gates. Detector request rate increased versus 8C-2H2 smoke (`0.02625 -> 0.03875`) but remained well under the `<0.10` gate; the 2I guards themselves are no-detector paths.

## Targeted Mini Dry-Run

Targeted video set:

- `dynamicBackground/fountain02`
- `dynamicBackground/fountain01`
- `shadow/cubicle`
- `nightVideos/bridgeEntry`
- `PTZ/continuousPan`
- `lowFramerate/tramCrossroad_1fps`

| Metric | 8C-2I targeted mini |
|---|---:|
| Jobs | 24/24 completed, 0 failed |
| FMeasure | 0.23247 |
| Event_F1 | 0.57761 |
| Activation | 0.50167 |
| Avg_FPS | 18.73201 |
| P95 latency ms | 467.01634 |
| Proposed intervention rate | 0.26667 |
| Proposed detector request rate | 0.02333 |
| Block-only rate | 0.24333 |
| Event/foreground block-only rate | 0.19833 |
| Normal-frame proposed interventions | 0 |
| Guard alignment | 1.00000 |
| Cubicle recall | 0.83838 |
| Cubicle unprotected event FN | 0 |
| bridgeEntry event FN | 0 |
| bridgeEntry detector budget max | 8 |
| continuousPan proposed intervention rate | 0.05000 |
| tramCrossroad_1fps proposed intervention rate | 0.01000 |
| tramCrossroad_1fps detector request rate | 0.00000 |
| fountain01 proposed intervention rate | 0.00000 |
| fountain01 detector request rate | 0.00000 |
| LowFramerate trim reclaimed proposals | 6 |
| LowFramerate retighten reclaimed proposals | 10 |
| fountain01 quiet-guard reclaimed proposals | 80 |

Targeted mini dry-run passed all required gates.

## Per-Video Risk Summary

| Video | Proposal rate | Detector request rate | Normal proposals | Event FN / unprotected FN | Detector budget max | Status |
|---|---:|---:|---:|---:|---:|---|
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | 0 | 0 / 0 | 0 | Quiet behavior restored; 80 proposals reclaimed. |
| `dynamicBackground/fountain02` | 0.40000 | 0.03000 | 0 | 0 / 0 | 3 | No normal-frame false intervention regression. |
| `shadow/cubicle` | 0.83000 | 0.02000 | 0 | 14 / 0 | 2 | Cubicle protected; recall 0.83838. |
| `nightVideos/bridgeEntry` | 0.31000 | 0.08000 | 0 | 0 / 0 | 8 | Protected; at detector budget cap but within gate. |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | 0 | 0 / 0 | 1 | Controlled at preferred cap. |
| `lowFramerate/tramCrossroad_1fps` | 0.01000 | 0.00000 | 0 | 3 / 2 | 0 | Retightened to 8C-2G behavior; lowFramerate guard active. |

The tramCrossroad per-video unprotected-FN count is present in the diagnostic summary, but the targeted 2I gate for that video is proposal/detector containment; the lowFramerate guard restored pressure to the 8C-2G level without detector requests.

## Comparison

| Metric | 8C-2G targeted mini | 8C-2H2 targeted mini | 8C-2I targeted mini |
|---|---:|---:|---:|
| Proposed intervention rate | 0.22167 | 0.35833 | 0.26667 |
| Detector request rate | 0.01500 | 0.05833 | 0.02333 |
| Normal-frame proposed interventions | 0 | 0 | 0 |
| Cubicle recall | 0.71717 | 0.82828 | 0.83838 |
| Cubicle unprotected event FN | 7 | 0 | 0 |
| bridgeEntry event FN | 0 | 0 | 0 |
| continuousPan proposal rate | 0.04000 | 0.05000 | 0.05000 |
| tramCrossroad_1fps proposal rate | 0.01000 | 0.18000 | 0.01000 |
| fountain01 proposal rate | 0.00000 | 0.38000 | 0.00000 |
| fountain01 detector request rate | 0.00000 | 0.15000 | 0.00000 |

8C-2I keeps the successful 8C-2H2 cubicle fix while restoring the two non-cubicle pressure failures:

- `dynamicBackground/fountain01`: `0.38000 -> 0.00000` proposal rate and `0.15000 -> 0.00000` detector request rate versus 8C-2H2.
- `lowFramerate/tramCrossroad_1fps`: `0.18000 -> 0.01000` proposal rate and `0.05000 -> 0.00000` detector request rate versus 8C-2H2.

## Gate Decision

| Gate | Smoke | Targeted mini |
|---|---|---|
| All jobs completed, 0 failed | Pass | Pass |
| Aggregate proposed intervention rate below 0.35 | Pass | Pass |
| Aggregate detector request rate below 0.10 | Pass | Pass |
| Normal-frame proposed interventions = 0 | Pass | Pass |
| Cubicle recall >= 0.80 | Pass | Pass |
| Cubicle unprotected event FN = 0 | Pass | Pass |
| bridgeEntry event FN = 0 | Pass | Pass |
| bridgeEntry detector budget max <= 8 | Pass | Pass |
| continuousPan proposal rate <= 0.05 | Pass | Pass |
| tramCrossroad_1fps controlled | Pass | Pass |
| fountain01 quiet behavior restored | Not applicable in smoke set | Pass |
| No forbidden validation launched | Pass | Pass |

Phase 8C-2I passes both dry-runs.

## Recommendation

Targeted mini live can be considered for explicit authorization next. Do not run it automatically, and do not expand to full CDnet or cross-dataset validation from this step. If live is authorized, use only a separate 8C-2I targeted mini live output root and keep accidental 8C-2E live artifacts excluded from official results.

## Step 2B Targeted Mini Live

Status: official targeted mini live completed but failed the strict live gate. Larger validation remains held.

Created live config and output root:

- `configs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live.yaml`
- `outputs/asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live/`

Commands:

```powershell
python src\run_experiment.py --config configs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live.yaml --max-jobs-per-run 8
python tools\compare_asmag_tr_controller_online_guarded.py --root outputs\asmag_tr_controller_online_guarded_cdnet_targeted_mini_2i_live
```

The live output folder was missing before this step, so no partial 8C-2I live artifacts were overwritten. Accidental 8C-2E live artifacts were not used.

### Live Aggregate Metrics

| Metric | 8C-2I targeted dry-run | 8C-2I targeted live |
|---|---:|---:|
| Jobs | 24/24 completed, 0 failed | 24/24 completed, 0 failed |
| FMeasure | 0.23247 | 0.35628 |
| Event_F1 | 0.57761 | 0.55840 |
| Activation | 0.50167 | 0.55167 |
| Avg_FPS | 18.73201 | 12.06588 |
| P95 latency ms | 467.01634 | 451.06938 |
| Intervention rate | 0.26667 | 0.26000 |
| Detector request rate | 0.02333 | 0.03000 |
| Block-only rate | 0.24333 | 0.23000 |
| Event/foreground block-only rate | 0.19833 | 0.18833 |
| Normal-frame interventions | 0 | 0 |
| Guard alignment | 1.00000 | 1.00000 |

Live behavior matched the dry-run pressure expectation for aggregate interventions, block-only pressure, normal-frame suppression, and guard alignment. Detector request remained well below the `<0.10` aggregate gate, though it rose from `0.02333` to `0.03000`.

### Live Per-Video Risk Summary

| Video | Live proposal/intervention rate | Live detector request rate | Key gate status |
|---|---:|---:|---|
| `dynamicBackground/fountain01` | 0.00000 | 0.00000 | Pass; quiet behavior preserved, 78 proposals reclaimed. |
| `dynamicBackground/fountain02` | 0.40000 | 0.03000 | Pass for requested gate; normal-frame false interventions = 0. |
| `shadow/cubicle` | 0.80000 | 0.06000 | Fail; recall 0.80808 but cubicle unprotected event FN = 1. |
| `nightVideos/bridgeEntry` | 0.31000 | 0.08000 | Pass; event FN = 0, detector budget max = 8. |
| `PTZ/continuousPan` | 0.05000 | 0.01000 | Pass; proposal/intervention rate at cap. |
| `lowFramerate/tramCrossroad_1fps` | 0.00000 | 0.00000 | Pass; event FN/unprotected FN = 0/0, trim and retighten active. |

### Live Gate Decision

| Gate | Result |
|---|---|
| 24/24 completed, 0 failed | Pass |
| Aggregate detector request rate < 0.10 | Pass |
| Normal-frame interventions = 0 | Pass |
| Cubicle recall >= 0.80 | Pass |
| Cubicle unprotected event FN = 0 | Fail: 1 |
| bridgeEntry event FN = 0 | Pass |
| bridgeEntry detector budget max <= 8 | Pass |
| continuousPan rate <= 0.05 | Pass |
| tramCrossroad_1fps rate <= 0.05 preferred, <= 0.10 hard | Pass |
| tramCrossroad_1fps detector request rate <= 0.02 | Pass |
| fountain01 rate <= 0.05 | Pass |
| fountain01 detector request rate <= 0.02 | Pass |
| fountain02 normal-frame false interventions = 0 | Pass |
| No broad detector-heavy behavior | Pass |
| No forbidden validation launched | Pass |

8C-2I does not pass targeted mini live because the strict cubicle unprotected event-FN gate requires `0`, and live produced `1`.

### Root Cause

The live cubicle miss is:

- `shadow/cubicle` frame `1560`
- Event state: `FN`
- Action: `CLOSED_EMPTY_P3_FALLBACK`
- Active event memory: `1`
- `ai_cubicle_like_event_continuity_active`: `0`, rejected by `event_continuity_signal_low`
- `ai_cubicle_micro_bump_active`: `0`, rejected by `micro_cap_exhausted`
- `ai_exact_cubicle_event_fn_pre_signal`: `0`
- `ai_exact_cubicle_event_fn_stabilizer_active`: `0`, rejected by `event_foreground_or_loss_score_low`
- Event/foreground score: `0.86748`
- Foreground-loss score: `0.68408`
- Foreground risk: `0.13333`

Interpretation: pressure cleanup and non-cubicle behavior held, but live application exposed one exact-cubicle event-FN protection gap after the micro-bump cap was exhausted and stabilizer/pre-signal thresholds did not cover frame 1560.

### Live Recommendation

Do not run larger validation. Step 3 targeted category dry-run remains held until a narrow exact-cubicle live stability fix is reviewed and dry-run validated. The next fix should target this exact live-only cubicle miss without increasing detector requests or touching non-cubicle guards.
