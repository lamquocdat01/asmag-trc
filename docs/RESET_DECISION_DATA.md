# Reset Decision Data — ONLINE_GUARDED về Step 4D6 Clean Base

Date: 2026-05-21
Scope: Data-only. Không sửa code, không chạy experiment.

---

## 1. Step 4D6 Baseline Gate Table (tất cả PASS)

Source: `docs/ASMAG_TR_CONTROLLER_ONLINE_GUARDED_STEP4D6_PARKING_FINAL_TRIM_REPORT.md`
Date: 2026-05-17. Subset: 14 videos × 4 pipelines = 56 jobs. Result: 56/56 completed, 0 failed.

| Gate | Value | Status |
|------|------:|--------|
| Planned jobs complete, 0 failed | 56/56, 0 failed | PASS |
| Aggregate detector request rate < 0.10 | 0.01071 | PASS |
| Normal-frame proposals = 0 | 0 | PASS |
| Guard alignment >= 0.95 | 1.00000 | PASS |
| **Parking** proposal <= 0.50 | **0.50000** | PASS |
| **Parking** detector <= 0.02 | 0.00000 | PASS |
| **Parking** unprotected FN <= 12 | **0** | PASS |
| Parking accidental FN/rescue trim = 0 | 0 / 0 | PASS |
| **SnowFall** proposal <= 0.45 | 0.36000 | PASS |
| **SnowFall** detector <= 0.03 | 0.00000 | PASS |
| **SnowFall** unprotected FN <= 6 acceptable | **1** | PASS |
| **LakeSide** proposal <= 0.50 | **0.50000** | PASS |
| **LakeSide** detector <= 0.02 | 0.00000 | PASS |
| **LakeSide** unprotected FN <= 8 preferred | **0** | PASS |
| Sofa proposal <= 0.35 preferred | 0.27000 | PASS |
| Sofa detector <= 0.03 | 0.00000 | PASS |
| Sofa unprotected FN <= 4 preferred | 0 | PASS |
| Port proposal (watch for Step 4E) | 0.37000 | PASS |
| Port detector (watch for Step 4E) | 0.07000 | PASS |
| Port unprotected FN | 0 | PASS |
| CopyMachine accepted gate | unprotected FN 4 | PASS |
| Turbulence2 accepted gate | unprotected FN 0 | PASS |
| TunnelExit accepted gate | unprotected FN 1 | PASS |
| **Cubicle** recall >= 0.80 and FN 0 | recall **0.87408**, unprotected FN **0** | PASS |
| ContinuousPan controlled | event FN 0 | PASS |
| IntermittentPan controlled | unprotected FN 0 | PASS |
| Fountain01 quiet | proposal 0.00, detector 0.00 | PASS |
| Fountain02 normal-frame false interventions = 0 | 0 | PASS |
| BridgeEntry event FN = 0 | 0 | PASS |
| No forbidden validation launched | none launched | PASS |

**Tổng kết Step 4D6: 29/29 gates PASS. Không có gate nào fail.**

Aggregate metrics tại 4D6: FMeasure 0.35061, Event_F1 0.67692, Activation 0.52429, Avg FPS 33.70033, P95 latency 258.68 ms.

---

## 2. Q1-SIC-1 State — Last Stable Event-Safety Base

Source: `docs/ASMAG_TR_Q1_SIC1_FINAL_ARBITRATION_REPORT.md`
Date: 2026-05-19. Decision: `FAIL_DRYRUN`.

Q1-SIC-1 là bước **đầu tiên** thêm final safety arbitration lên Step 4D6. Nó fail vì snowFall 1150 telemetry mismatch — đây là nguồn gốc của toàn bộ vòng lặp R1 → R2 → R3 → R3B → R3C → R3D.

### Per-video tại Q1-SIC-1

| Video | Proposal | Detector | Unprotected FN | Status vs 4D6 |
|-------|----------|----------|----------------|---------------|
| intermittentObjectMotion/parking | 0.46 | 0.00 | 0 | **BETTER** (4D6 = 0.50 / 0) |
| badWeather/snowFall | 0.36 | 0.00 | 1 | SAME (still 1 unprotected FN) |
| thermal/lakeSide | 0.50 | 0.00 | 0 | SAME |
| shadow/cubicle | 0.91 | 0.02 | 0 | recall watch — SAME |
| lowFramerate/port_0_17fps | 0.40 | 0.08 | 2 | WORSE (4D6 = 0.37 / 0.07 / 0) |
| shadow/copyMachine | 0.52 | 0.00 | 0 | BETTER (4D6 = 0.46 / 4 unprotected) |
| lowFramerate/tunnelExit_0_35fps | 0.35 | 0.00 | 0 | BETTER (4D6 = 0.31 / 1) |

**Kết luận Q1-SIC-1**: parking được cải thiện về proposal (0.46 vs 0.50), copyMachine và tunnelExit cũng cải thiện. Nhưng **snowFall 1150 vẫn là unprotected FN với label NO_CHANGE** — đây là lý do fail duy nhất mà Q1-SIC-1 không thể frozen.

---

## 3. Số lượng code changes từ Step 4D6 đến R3D

### Tình trạng commit

Toàn bộ work từ Step 4D6 đến R3D **chưa được commit**. Tất cả nằm trong working tree.

| Mốc | Ngày commit | Hash |
|-----|------------|------|
| Last commit chứa run_experiment.py (Phase 8C-1B) | 2026-05-11 | `79130fa` |
| Step 4D6 bắt đầu | 2026-05-17 | uncommitted |
| Q1-SIC-0 → R3D | 2026-05-17 – 2026-05-20 | uncommitted |
| Hiện tại | 2026-05-21 | uncommitted |

### Kích thước run_experiment.py: committed vs working tree

| | Committed HEAD (79130fa, 2026-05-11) | Working tree hiện tại |
|-|--------------------------------------|----------------------|
| Số dòng | 2,411 | **21,987** |
| `q1_sic` references | 0 | **417** |
| `observer` references | 0 | **57** |
| `probe` references | 0 | **246** |

**Delta (working tree vs committed HEAD)**:
- `git diff --stat HEAD -- src/run_experiment.py`: **+20,886 insertions / −1,310 deletions**
- Net gain: **+19,576 dòng** (tăng 812% so với bản committed)

---

## 4. snowFall Frame 1150: So sánh 4D6 vs Q1-SIC-1 vs R3D (cả hai variant)

Frame 1150 là "canary frame" — nó có `active_event_memory=1`, `ai_intervention_risk_high=1`, và là unprotected FN tại 4D6. Mọi Q1-SIC phase đều cố gắng protect frame này.

| Field | 4D6 | Q1-SIC-1 | R3D baseline (observer=off) | R3D observer_purity (observer=on) |
|-------|-----|----------|-----------------------------|------------------------------------|
| action_label | DETECT_ACC | DETECT_ACC | DETECT_ACC | **CLOSED_EMPTY_ACC** |
| action_reason | policy | policy | policy | overload_reuse |
| yolo_called | 1 | 1 | 1 | **0** |
| activation | 1 | 1 | 1 | **0** |
| active_event_memory | 1 | 1 | 1 | 1 |
| ai_intervention_risk_high | 1 | 1 | 1 | **1** |
| ai_detector_needed_pred | 1 | 1 | 1 | **0** |
| q1_sic_arbitration_active | n/a | 0 | 0 | **1** |
| q1_sic_arbitration_label | n/a | NO_CHANGE | NO_CHANGE | **FORCE_PROTECT_EVENT_MEMORY** |
| q1_sic_pre_protection_label | n/a | unprotected_fn | unprotected_fn | unprotected_fn |
| q1_sic_post_protection_label | n/a | unprotected_fn | unprotected_fn | **protected_event_fn** |
| q1_sic_observer_isolated_enabled | n/a | (no col) | 0 | **1** |
| q1_sic_detector_action_probe_enabled | n/a | (no col) | 1 | 1 |

**Quan sát quan trọng**:

1. **4D6 → Q1-SIC-1 → R3D baseline: KHÔNG thay đổi** — frame 1150 vẫn là `DETECT_ACC / unprotected_fn / NO_CHANGE`. Q1-SIC-1 thêm telemetry nhưng không protect frame này.
2. **R3D observer=on: thay đổi hoàn toàn** — frame 1150 trở thành `CLOSED_EMPTY_ACC / FORCE_PROTECT_EVENT_MEMORY`. Điều này có nghĩa là **observer flag đang thay đổi trajectory của frame này**, không chỉ thêm telemetry.
3. **Hệ quả**: Enabling observer flag không chỉ "quan sát" — nó làm thay đổi `ai_detector_needed_pred` (1→0) và `action_label` (DETECT→CLOSED_EMPTY), tức là observer đang can thiệp vào state trước khi frame_metrics row được tính.

### R3D Overall Behavior Delta (baseline vs observer)

| Metric | Value |
|--------|------:|
| Behavior delta rows | **480** (trên 1400 guarded rows) |
| Behavior delta cells | **1,250** |
| Action-label deltas | 393 |
| Proposal deltas | 213 |
| YOLO-called deltas | 254 |
| Q1-label deltas | 36 |
| Normal-frame intervention indicator deltas | **40** |
| Live-probe delta rows | **598** |
| Live-probe delta cells | **3,204** |

**Kết luận R3D**: `FAIL_OBSERVER_IDENTITY`. Observer flag gây 480 behavior delta rows ngay trong paired same-source run. Observer chưa thực sự isolated.

---

## 5. Phân tích: Code nào PHẢI giữ — Code nào có thể xóa

### 5.1. Code PHẢI GIỮ khi reset về 4D6 clean base

Những phần code này đã được validate bởi gate table 4D6 (29/29 PASS):

| Code block | Mô tả | Output folder verify |
|-----------|--------|---------------------|
| **Step 4B4 lakeSide carry-over** | lakeSide unprotected FN = 0 (Pass) | `step4b4_*` |
| **Step 4C sofa rescue** | sofa unprotected FN = 0 (Pass) | `step4c_*` |
| **Step 4D3 parking trim** | 4 frame post-preservation trims, accidental=0 | `step4d3_*` |
| **Step 4D5 post-lock soft-candidate trim** | 4 trims, soft candidates = 12 | `step4d5_*` |
| **Step 4D6 final one-frame extra trim** | parking proposal giảm từ 0.51 → 0.50 | `step4d6_*` |
| **Port detector watch logic (4E-era)** | port unprotected FN = 0 tại 4D6 | `step4d6_*` |
| **SnowFall cap behavior (4D3)** | 1 unprotected FN accepted, cap exhausted after 4D3 | `step4d6_*` |

### 5.2. Code CÓ THỂ XÓA khi reset (Q1-SIC additions, tất cả đều FAIL)

| Code block | Keywords | Ref count | Failure |
|-----------|----------|-----------|---------|
| `final_safety_arbitration(...)` function | `q1_sic_final_arbitration_enabled` | ~50 | FAIL_DRYRUN (Q1-SIC-1) |
| Q1-SIC config flags parsing | `q1_sic_shadow_only`, `q1_sic_arbitration_active`, v.v. | ~100 | tất cả Q1-SIC phases fail |
| Q1-SIC telemetry columns (17 cols added) | `q1_sic_arbitration_label`, `q1_sic_pre_action`, v.v. | ~80 | overhead không có kết quả |
| Q1-SIC-1B empty-detect proxy | `q1_sic_event_risk_empty_detect_proxy` | ~20 | FAIL_DRYRUN (Q1-SIC-1B) |
| Stable detector-action probe snapshot | `q1_sic_detector_action_probe_stable_snapshot_enabled` | ~30 | FAIL_PROBE_SNAPSHOT (C1R2) |
| CopyMachine restore shim | `q1_sic_copyMachine_restore_*` | ~15 | FAIL_RESTORE_BASE (C1C1) |
| Port watch telemetry restore | `q1_sic_port_watch_telemetry_restore_*` | ~15 | FAIL_PROBE_REGRESSION (C1C1R) |
| Observer isolation build/merge | `build_q1_sic_detector_action_observer_row`, `q1_sic_observer_isolated_enabled` | ~57 | FAIL_OBSERVER_IDENTITY (R3D) |
| Live detector-action probe helper | `_apply_q1_sic_detector_action_probe`, `probe` | ~246 | FAIL_BEHAVIOR_IDENTITY (R3) |
| Observer pressure memory | `q1_sic_observer_pressure_memory_enabled` | ~10 | disabled/unused |

**Tổng**: ~623 references cần xóa = 417 `q1_sic` + 57 `observer` + 246 `probe` (có overlap).

### 5.3. Ước tính dòng sau reset

Nếu xóa toàn bộ Q1-SIC additions:
- Committed HEAD: 2,411 dòng
- 4D6 additions (chưa commit): ước tính ~500-800 dòng thực sự cần thiết (4B4, 4C, 4D3-6, Step 4E watch telemetry)
- Sau reset: dự kiến **~3,000–3,500 dòng** thay vì 21,987

---

## 6. Kết luận tổng hợp

### Câu hỏi: Có nên reset về Step 4D6 không?

**Bằng chứng ủng hộ reset:**

1. **Step 4D6 là điểm ổn định duy nhất với 29/29 gates PASS** trong toàn bộ lịch sử Q1-SIC.
2. **Tất cả 8 Q1-SIC phases (1 → 1A → 1B → 1C → 1C1 → 1C1R → C1R2 → R3 → R3B → R3C → R3D) đều FAIL** mà không có phase nào tiến thêm được một gate thực sự.
3. **run_experiment.py hiện tại có 21,987 dòng** — gấp 9 lần bản committed (2,411 dòng). Toàn bộ 19,576 dòng thêm vào chưa commit và không có phase nào pass.
4. **Observer flag (R3D) vẫn gây 480 behavior delta rows** trong paired same-source test — tức là observer không thực sự isolated dù đã sửa 5 lần.
5. **snowFall frame 1150 là unprotected FN tại 4D6** và vẫn là unprotected FN tại Q1-SIC-1, R3D baseline — không có phase nào thực sự fix frame này mà không làm vỡ behavior khác.

**Bằng chứng cần lưu ý khi reset:**

1. **Q1-SIC-1 cải thiện parking** (0.46 vs 4D6's 0.50) và copyMachine (0 vs 4 unprotected FN). Phần này là kết quả tốt nhưng đi kèm với code quá phức tạp.
2. **Port unprotected FN tại Q1-SIC-1 là 2** (4D6 = 0) — nếu reset, port phải được xử lý qua Step 4E clean mà không có Q1-SIC overhead.
3. **Toàn bộ Step 4E (4E2-4E6) cũng fail** về port. Port vẫn là vấn đề chưa giải quyết dù không liên quan đến Q1-SIC.

**Khuyến nghị:**

Reset về Step 4D6 base là quyết định hợp lý với điều kiện:
- Lưu lại toàn bộ output folders hiện có (không xóa) để tham chiếu
- Lưu Q1-SIC logic vào một file riêng (không trong run_experiment.py) trước khi xóa
- Sau khi reset, implement Step 4E port retighten lại từ đầu, lần này đơn giản hơn và không kết hợp với observer/probe
- snowFall frame 1150 cần một approach khác: thay vì observer isolation, có thể dùng direct arbitration đơn giản không cần probe infrastructure

---

*Data collected: 2026-05-21. Source: docs/*, outputs/*/raw_results, git log, wc -l, grep -c.*
