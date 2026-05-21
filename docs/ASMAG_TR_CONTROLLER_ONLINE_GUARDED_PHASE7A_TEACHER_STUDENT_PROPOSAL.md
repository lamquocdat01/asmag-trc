# ASMAG_TR_CONTROLLER_ONLINE_GUARDED Phase 7A Teacher-Student Proposal

## Research Question

Can teacher-guided action selection improve PTZ/global-motion scenes while preserving Phase 5B/6C safety guards?

## Teacher Evidence

Teachers inspected: `P3_MOG2`, `ASMAG_TR_CONTROLLER`, and old `ONLINE_CALIBRATED`. The table below compares teachers against guarded on key smoke and targeted videos.

| dataset   | category          | video             | pipeline                           |   FMeasure |   Event_F1 |   Avg_FPS |   P95_latency_ms |   delta_F_vs_guarded | beats_guarded_F   | best_teacher_by_FMeasure   |
|:----------|:------------------|:------------------|:-----------------------------------|-----------:|-----------:|----------:|-----------------:|---------------------:|:------------------|:---------------------------|
| smoke     | nightVideos       | bridgeEntry       | ASMAG_TR_CONTROLLER                |     0.3095 |     0.9744 |    5.002  |          224.332 |               0.151  | True              | ASMAG_TR_CONTROLLER        |
| smoke     | nightVideos       | bridgeEntry       | P3_MOG2                            |     0.3095 |     0.9744 |    5.0511 |          228.586 |               0.151  | True              | ASMAG_TR_CONTROLLER        |
| smoke     | nightVideos       | bridgeEntry       | ONLINE_CALIBRATED                  |     0.2397 |     0.9744 |    7.5271 |          258.644 |               0.0813 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | nightVideos       | bridgeEntry       | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.1585 |     0.9744 |   16.3382 |          234.175 |               0      | False             | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | continuousPan     | ASMAG_TR_CONTROLLER                |     0.2347 |     0.2906 |    4.5736 |          248.515 |               0.0811 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | continuousPan     | ONLINE_CALIBRATED                  |     0.2347 |     0.2906 |    3.4338 |          318.682 |               0.0811 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | continuousPan     | P3_MOG2                            |     0.2347 |     0.2906 |    4.6836 |          258.697 |               0.0811 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | continuousPan     | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.1536 |     0.2931 |    5.5848 |          300.607 |               0      | False             | ASMAG_TR_CONTROLLER        |
| smoke     | shadow            | cubicle           | ASMAG_TR_CONTROLLER                |     0.2824 |     0.819  |  156.396  |          246.607 |               0.0874 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | shadow            | cubicle           | P3_MOG2                            |     0.2824 |     0.819  |  302.228  |          251.615 |               0.0874 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | shadow            | cubicle           | ONLINE_CALIBRATED                  |     0.2235 |     0.7705 |   39.8783 |          234.761 |               0.0285 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | shadow            | cubicle           | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.195  |     0.736  |   41.9228 |          231.09  |               0      | False             | ASMAG_TR_CONTROLLER        |
| smoke     | dynamicBackground | fountain02        | ASMAG_TR_CONTROLLER                |     0.7543 |     0.8772 |  104.307  |          243.168 |               0.0455 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | dynamicBackground | fountain02        | P3_MOG2                            |     0.7543 |     0.8772 |  157.85   |          198.741 |               0.0455 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | dynamicBackground | fountain02        | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.7088 |     0.6667 |   39.9452 |          225.711 |               0      | False             | ASMAG_TR_CONTROLLER        |
| smoke     | dynamicBackground | fountain02        | ONLINE_CALIBRATED                  |     0.6541 |     0.6866 |   39.8827 |          240.557 |              -0.0547 | False             | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | twoPositionPTZCam | ASMAG_TR_CONTROLLER                |     0.8542 |     0.8077 |   17.8605 |          212.135 |               0.0834 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | twoPositionPTZCam | P3_MOG2                            |     0.8542 |     0.8077 |   10.9842 |          208.62  |               0.0834 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | twoPositionPTZCam | ONLINE_CALIBRATED                  |     0.8107 |     0.8025 |    6.7892 |          322.191 |               0.0399 | True              | ASMAG_TR_CONTROLLER        |
| smoke     | PTZ               | twoPositionPTZCam | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.7708 |     0.7925 |   14.9741 |          244.348 |               0      | False             | ASMAG_TR_CONTROLLER        |
| targeted  | nightVideos       | bridgeEntry       | ASMAG_TR_CONTROLLER                |     0.3095 |     0.9744 |    4.8562 |          308.928 |               0.1405 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | nightVideos       | bridgeEntry       | P3_MOG2                            |     0.3095 |     0.9744 |    4.6636 |          391.115 |               0.1405 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | nightVideos       | bridgeEntry       | ONLINE_CALIBRATED                  |     0.2397 |     0.9744 |    6.6577 |          402.708 |               0.0708 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | nightVideos       | bridgeEntry       | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.169  |     0.9744 |   22.3864 |          392.551 |               0      | False             | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | continuousPan     | ASMAG_TR_CONTROLLER                |     0.2347 |     0.2906 |    4.4023 |          347.815 |               0.1132 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | continuousPan     | ONLINE_CALIBRATED                  |     0.2347 |     0.2906 |    3.0093 |          527.529 |               0.1132 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | continuousPan     | P3_MOG2                            |     0.2347 |     0.2906 |    4.5246 |          331.981 |               0.1132 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | continuousPan     | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.1215 |     0.2906 |   18.7528 |          333.952 |               0      | False             | ASMAG_TR_CONTROLLER        |
| targeted  | shadow            | cubicle           | ASMAG_TR_CONTROLLER                |     0.2824 |     0.819  |  145.684  |          312.493 |               0.0825 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | shadow            | cubicle           | P3_MOG2                            |     0.2824 |     0.819  |  147.005  |          295.38  |               0.0825 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | shadow            | cubicle           | ONLINE_CALIBRATED                  |     0.2235 |     0.7705 |   44.6412 |          344.24  |               0.0236 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | shadow            | cubicle           | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.1999 |     0.7154 |   39.0105 |          400.073 |               0      | False             | ASMAG_TR_CONTROLLER        |
| targeted  | dynamicBackground | fountain02        | ASMAG_TR_CONTROLLER                |     0.7543 |     0.8772 |  205.229  |          249.268 |               0.0432 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | dynamicBackground | fountain02        | P3_MOG2                            |     0.7543 |     0.8772 |  203.113  |          210.93  |               0.0432 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | dynamicBackground | fountain02        | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.711  |     0.6667 |   41.916  |          294.796 |               0      | False             | ASMAG_TR_CONTROLLER        |
| targeted  | dynamicBackground | fountain02        | ONLINE_CALIBRATED                  |     0.6544 |     0.6866 |   40.331  |          311.378 |              -0.0566 | False             | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | intermittentPan   | ASMAG_TR_CONTROLLER                |     0.4989 |     0.8205 |   18.1862 |          350.015 |               0.3313 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | intermittentPan   | P3_MOG2                            |     0.4989 |     0.8205 |   12.3308 |          301.594 |               0.3313 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | intermittentPan   | ONLINE_CALIBRATED                  |     0.3548 |     0.8466 |    6.5392 |          497.571 |               0.1873 | True              | ASMAG_TR_CONTROLLER        |
| targeted  | PTZ               | intermittentPan   | ASMAG_TR_CONTROLLER_ONLINE_GUARDED |     0.1676 |     0.76   |   27.3709 |          324.412 |               0      | False             | ASMAG_TR_CONTROLLER        |

## Findings

- In continuousPan and several targeted PTZ cases, the best teacher is more detector-like than Guarded. This supports imitating detector cadence under low PTZ trust rather than increasing reuse or lightweight P3.
- Targeted diagnosis showed `zoomInZoomOut`, `intermittentPan`, and `continuousPan` collapse when ACC/raw candidate quality is accepted without temporal/geometric trust. Teacher behavior says the policy should recover detector-like cadence before it experiments with cheap actions.
- `twoPositionPTZCam` is near target after Phase 6C; teacher guidance there should be used only for jump/reset handling, not broad continuous-pan relaxation.
- Non-PTZ scenes and bridgeEntry do not need a learned PTZ policy. Their existing deterministic safety and fast-path behavior should remain first-class guards.

## Proposed Teacher-Student Shape

Use a three-layer policy:

1. Deterministic safety guards first: no closed-empty during active event/global motion, no reuse under low compensated/geometric trust, no lightweight P3 in PTZ, detector cadence floor when frames since detector is high.
2. Teacher-distilled ranked selector second: choose among `DETECT_ACC`, `FALLBACK_P3_GUARD`, and `LIGHTWEIGHT_MASK_ACC` using runtime trust, geometry, candidate quality, and cadence state.
3. Final sanitizer third: preserve Phase 5B event safety, PTZ closed-empty kill, non-PTZ suppression, and existing diagnostics.

## Learned Policy Justification

A learned or ranked policy is justified as a research direction because the same nominal action can be good or dangerous depending on trust state. However, the current evidence is too small and observational for a direct deployed classifier. Phase 7B should implement a distilled deterministic rule set from the teacher/oracle findings, then continue collecting teacher-labeled telemetry.

## PTZ Targeted Status

PTZ-targeted is not allowed from this phase. This was research-only and no validation smoke was run.
