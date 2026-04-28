import cv2
import numpy as np
import math

def morph(mask):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

def pixel_dispersion_entropy(binary_roi):
    y, x = np.where(binary_roi > 0)
    if len(x) < 10:
        return 10.0
    cx, cy = np.mean(x), np.mean(y)
    d = np.sqrt((x-cx)**2 + (y-cy)**2)
    s = np.sum(d)
    if s == 0:
        return 0.0
    p = d / s
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def component_filter(mask, min_area, entropy_threshold=8.5):
    num, labels, stats, _ = cv2.connectedComponentsWithStats((mask>0).astype(np.uint8), 8)
    clean = np.zeros_like(mask, dtype=np.uint8)
    kept, entropies = 0, []
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area:
            continue
        comp = (labels == i).astype(np.uint8) * 255
        ent = pixel_dispersion_entropy(comp)
        entropies.append(ent)
        # Keep compact components and do not over-reject, because CDnet recall is important
        if ent <= entropy_threshold or area > min_area * 4:
            clean[labels == i] = 255
            kept += 1
    return clean, kept, float(np.mean(entropies)) if entropies else 0.0

def precision_component_filter(mask, cfg, image_area):
    min_area = max(1, int(float(cfg.get("min_component_area_ratio", 0.0003)) * image_area))
    max_area = max(min_area, int(float(cfg.get("max_component_area_ratio", 0.025)) * image_area))
    max_aspect = float(cfg.get("max_aspect_ratio", 8.0))
    min_solidity = float(cfg.get("min_solidity", 0.12))

    num, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    clean = np.zeros_like(mask, dtype=np.uint8)
    kept = 0
    removed_large = 0
    removed_bad_shape = 0

    for i in range(1, num):
        area = int(stats[i, cv2.CC_STAT_AREA])
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        if area < min_area or area > max_area:
            removed_large += 1
            continue

        aspect = max(w / max(1, h), h / max(1, w))
        comp = ((labels == i).astype(np.uint8)) * 255
        contours, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_area = sum(cv2.contourArea(c) for c in contours)
        hull_area = 0.0
        for c in contours:
            if len(c) >= 3:
                hull_area += cv2.contourArea(cv2.convexHull(c))
        solidity = contour_area / hull_area if hull_area > 0 else 0.0

        if aspect > max_aspect or solidity < min_solidity:
            removed_bad_shape += 1
            continue

        clean[labels == i] = 255
        kept += 1

    return clean, kept, removed_large, removed_bad_shape

def keep_components_with_support(mask, support):
    num, labels, _, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    clean = np.zeros_like(mask, dtype=np.uint8)
    for i in range(1, num):
        comp = labels == i
        if np.any(support[comp] > 0):
            clean[comp] = 255
    return clean

class FrameDiffGate:
    def __init__(self, threshold=30, min_area_ratio=0.001):
        self.threshold = threshold
        self.min_area_ratio = min_area_ratio

    def process(self, frame, prev_frame, state=None):
        h,w = frame.shape[:2]
        if prev_frame is None:
            return False, np.zeros((h,w), dtype=np.uint8), {"motion_area": 0, "gate_score": 0}
        g1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(cv2.absdiff(g1,g2), self.threshold, 255, cv2.THRESH_BINARY)
        mask = morph(mask)
        area = int(np.sum(mask > 0))
        min_area = int(h*w*self.min_area_ratio)
        return area >= min_area, mask, {"motion_area": area, "gate_score": min(1.0, area/(min_area*5+1))}

class MOG2Gate:
    def __init__(self, min_area_ratio=0.001):
        self.bg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
        self.min_area_ratio = min_area_ratio

    def process(self, frame, prev_frame=None, state=None):
        h,w = frame.shape[:2]
        raw = self.bg.apply(frame, learningRate=0.01)
        _, mask = cv2.threshold(raw, 200, 255, cv2.THRESH_BINARY)
        mask = morph(mask)
        area = int(np.sum(mask > 0))
        min_area = int(h*w*self.min_area_ratio)
        return area >= min_area, mask, {"motion_area": area, "gate_score": min(1.0, area/(min_area*5+1))}

class ASMAGPlusGate:
    def __init__(self, cfg):
        self.bg_mog2 = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
        self.bg_knn = cv2.createBackgroundSubtractorKNN(history=500, dist2Threshold=400, detectShadows=False)
        self.cfg = cfg
        self.last_debug_masks = {}
        self.state = {
            "gate_open": False,
            "closed_count": 0,
            "last_detection_age": 999,
            "prev_illumination": None
        }

    def process(self, frame, prev_frame=None, state=None):
        h,w = frame.shape[:2]
        min_area = max(20, int(h*w*float(self.cfg.get("min_area_ratio", 0.001))))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        illum = float(np.mean(gray))
        prev_illum = self.state["prev_illumination"] if self.state["prev_illumination"] is not None else illum
        illum_diff = abs(illum - prev_illum)
        self.state["prev_illumination"] = illum

        # Source 1: FrameDiff
        fd_mask = np.zeros((h,w), dtype=np.uint8)
        if prev_frame is not None:
            gprev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            _, fd_mask = cv2.threshold(cv2.absdiff(gprev, gray), 25, 255, cv2.THRESH_BINARY)

        # Source 2: MOG2
        mog = self.bg_mog2.apply(frame, learningRate=0.01 if illum_diff < 25 else 0.05)
        _, mog_mask = cv2.threshold(mog, 200, 255, cv2.THRESH_BINARY)

        # Source 3: KNN
        knn = self.bg_knn.apply(frame, learningRate=0.01 if illum_diff < 25 else 0.05)
        _, knn_mask = cv2.threshold(knn, 200, 255, cv2.THRESH_BINARY)

        # gate mask prioritizes recall
        gate_mask = cv2.bitwise_or(fd_mask, cv2.bitwise_or(mog_mask, knn_mask))
        gate_mask = morph(gate_mask)
        gate_mask_before_filter = gate_mask.copy()

        # filter mask prioritizes precision
        filter_mask, kept_components, comp_entropy = component_filter(
            gate_mask, min_area=min_area, entropy_threshold=float(self.cfg.get("entropy_threshold", 8.5))
        )
        if np.sum(filter_mask > 0) == 0:
            filter_mask = gate_mask  # fallback to prevent too-low recall

        self.last_debug_masks = {
            "fd_mask": fd_mask.copy(),
            "mog_mask": mog_mask.copy(),
            "knn_mask": knn_mask.copy(),
            "gate_mask_before_filter": gate_mask_before_filter.copy(),
            "filter_mask_after_component": filter_mask.copy(),
        }

        motion_area = int(np.sum(gate_mask > 0))
        motion_density = motion_area / float(h*w)
        area_score = min(1.0, motion_area / float(min_area*6 + 1))
        illum_penalty = min(0.6, illum_diff / 80.0)
        entropy_noise = min(1.0, comp_entropy / 12.0) if comp_entropy > 0 else 0.0
        temporal_persistence = 1.0 if self.state["last_detection_age"] < int(self.cfg.get("recent_object_memory", 30)) else 0.0

        gate_score = (
            0.45 * area_score +
            0.20 * min(1.0, motion_density * 80) +
            0.20 * temporal_persistence -
            0.10 * entropy_noise -
            0.15 * illum_penalty
        )
        gate_score = max(0.0, min(1.0, gate_score))

        open_t = float(self.cfg.get("open_threshold", 0.55))
        close_t = float(self.cfg.get("close_threshold", 0.30))

        if gate_score >= open_t:
            self.state["gate_open"] = True
        elif gate_score <= close_t:
            self.state["gate_open"] = False
        # else keep previous state (hysteresis)

        watchdog = False
        if not self.state["gate_open"]:
            self.state["closed_count"] += 1
            trigger = int(self.cfg.get("watchdog_closed_frames", 12))
            interval = int(self.cfg.get("watchdog_interval", 6))
            if self.state["closed_count"] >= trigger and self.state["closed_count"] % interval == 0:
                watchdog = True
        else:
            self.state["closed_count"] = 0

        gate_open = self.state["gate_open"] or watchdog
        info = {
            "gate_score": gate_score,
            "motion_area": motion_area,
            "motion_density": motion_density,
            "illumination_diff": illum_diff,
            "component_entropy_mean": comp_entropy,
            "kept_components": kept_components,
            "watchdog_triggered": int(watchdog)
        }
        return gate_open, filter_mask, info

    def update_after_detection(self, detected):
        if detected:
            self.state["last_detection_age"] = 0
        else:
            self.state["last_detection_age"] += 1

    def reset_runtime_state(self):
        self.state["gate_open"] = False
        self.state["closed_count"] = 0
        self.state["last_detection_age"] = 999

class ASMAGPlusPrecisionGate(ASMAGPlusGate):
    def process(self, frame, prev_frame=None, state=None):
        h, w = frame.shape[:2]
        image_area = h * w
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        illum = float(np.mean(gray))
        prev_illum = self.state["prev_illumination"] if self.state["prev_illumination"] is not None else illum
        illum_diff = abs(illum - prev_illum)
        self.state["prev_illumination"] = illum

        fd_mask = np.zeros((h, w), dtype=np.uint8)
        if prev_frame is not None:
            gprev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            _, fd_mask = cv2.threshold(cv2.absdiff(gprev, gray), 25, 255, cv2.THRESH_BINARY)

        mog = self.bg_mog2.apply(frame, learningRate=0.01 if illum_diff < 25 else 0.05)
        _, mog_mask = cv2.threshold(mog, 200, 255, cv2.THRESH_BINARY)
        knn = self.bg_knn.apply(frame, learningRate=0.01 if illum_diff < 25 else 0.05)
        _, knn_mask = cv2.threshold(knn, 200, 255, cv2.THRESH_BINARY)

        fd_mask = morph(fd_mask)
        mog_mask = morph(mog_mask)
        knn_mask = morph(knn_mask)

        fd_area = int(np.sum(fd_mask > 0))
        mog_area = int(np.sum(mog_mask > 0))
        knn_area = int(np.sum(knn_mask > 0))
        knn_gate_limit = float(self.cfg.get("knn_max_area_ratio_for_gate", 0.03)) * image_area
        knn_filter_limit = float(self.cfg.get("knn_max_area_ratio_for_filter", 0.02)) * image_area
        knn_suppressed_gate = int(knn_area > knn_gate_limit)
        knn_suppressed_filter = int(knn_area > knn_filter_limit)

        gate_knn = np.zeros_like(knn_mask) if knn_suppressed_gate else knn_mask
        gate_mask = cv2.bitwise_or(fd_mask, cv2.bitwise_or(mog_mask, gate_knn))
        gate_mask = morph(gate_mask)

        fusion_mode = self.cfg.get("fusion_mode", "majority_2_of_3")
        if fusion_mode == "mog2_primary":
            if knn_suppressed_filter:
                filter_seed = mog_mask.copy()
            else:
                filter_seed = cv2.bitwise_or(mog_mask, cv2.bitwise_and(fd_mask, knn_mask))
        else:
            knn_for_filter = np.zeros_like(knn_mask) if knn_suppressed_filter else knn_mask
            votes = (fd_mask > 0).astype(np.uint8) + (mog_mask > 0).astype(np.uint8) + (knn_for_filter > 0).astype(np.uint8)
            filter_seed = (votes >= 2).astype(np.uint8) * 255

        filter_mask, kept_components, removed_large, removed_bad_shape = precision_component_filter(
            filter_seed, self.cfg, image_area
        )
        if np.sum(filter_mask > 0) == 0 and np.sum(filter_seed > 0) > 0:
            filter_mask = filter_seed

        motion_area = int(np.sum(gate_mask > 0))
        min_area = max(20, int(image_area * float(self.cfg.get("min_area_ratio", 0.001))))
        motion_density = motion_area / float(image_area)
        area_score = min(1.0, motion_area / float(min_area * 6 + 1))
        illum_penalty = min(0.6, illum_diff / 80.0)
        temporal_persistence = 1.0 if self.state["last_detection_age"] < int(self.cfg.get("recent_object_memory", 30)) else 0.0
        gate_score = 0.45 * area_score + 0.20 * min(1.0, motion_density * 80) + 0.20 * temporal_persistence - 0.15 * illum_penalty
        gate_score = max(0.0, min(1.0, gate_score))

        open_t = float(self.cfg.get("open_threshold", 0.55))
        close_t = float(self.cfg.get("close_threshold", 0.30))
        if gate_score >= open_t:
            self.state["gate_open"] = True
        elif gate_score <= close_t:
            self.state["gate_open"] = False

        watchdog = False
        if not self.state["gate_open"]:
            self.state["closed_count"] += 1
            trigger = int(self.cfg.get("watchdog_closed_frames", 12))
            interval = int(self.cfg.get("watchdog_interval", 6))
            if self.state["closed_count"] >= trigger and self.state["closed_count"] % interval == 0:
                watchdog = True
        else:
            self.state["closed_count"] = 0

        gate_open = self.state["gate_open"] or watchdog
        self.last_debug_masks = {
            "fd_mask": fd_mask.copy(),
            "mog_mask": mog_mask.copy(),
            "knn_mask": knn_mask.copy(),
            "gate_mask_before_filter": gate_mask.copy(),
            "filter_mask_after_component": filter_mask.copy(),
        }
        info = {
            "gate_score": gate_score,
            "motion_area": motion_area,
            "motion_density": motion_density,
            "illumination_diff": illum_diff,
            "component_entropy_mean": 0.0,
            "kept_components": kept_components,
            "watchdog_triggered": int(watchdog),
            "fd_area": fd_area,
            "mog_area": mog_area,
            "knn_area": knn_area,
            "gate_area": int(np.sum(gate_mask > 0)),
            "filter_area": int(np.sum(filter_mask > 0)),
            "final_area": int(np.sum(filter_mask > 0)),
            "fusion_mode": fusion_mode,
            "knn_suppressed_gate": knn_suppressed_gate,
            "knn_suppressed_filter": knn_suppressed_filter,
            "removed_large_components": removed_large,
            "removed_bad_shape_components": removed_bad_shape,
        }
        return gate_open, filter_mask, info

class ASMAGPlusBalancedGate(ASMAGPlusGate):
    def process(self, frame, prev_frame=None, state=None):
        h, w = frame.shape[:2]
        image_area = h * w
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        illum = float(np.mean(gray))
        prev_illum = self.state["prev_illumination"] if self.state["prev_illumination"] is not None else illum
        illum_diff = abs(illum - prev_illum)
        self.state["prev_illumination"] = illum

        fd_mask = np.zeros((h, w), dtype=np.uint8)
        if prev_frame is not None:
            gprev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            _, fd_mask = cv2.threshold(cv2.absdiff(gprev, gray), 25, 255, cv2.THRESH_BINARY)

        mog = self.bg_mog2.apply(frame, learningRate=0.01 if illum_diff < 25 else 0.05)
        _, mog_mask = cv2.threshold(mog, 200, 255, cv2.THRESH_BINARY)
        knn = self.bg_knn.apply(frame, learningRate=0.01 if illum_diff < 25 else 0.05)
        _, knn_mask = cv2.threshold(knn, 200, 255, cv2.THRESH_BINARY)

        fd_mask = morph(fd_mask)
        mog_mask = morph(mog_mask)
        knn_mask = morph(knn_mask)
        fd_area = int(np.sum(fd_mask > 0))
        mog_area = int(np.sum(mog_mask > 0))
        knn_area = int(np.sum(knn_mask > 0))

        knn_gate_limit = float(self.cfg.get("knn_max_area_ratio_for_gate", 0.03)) * image_area
        knn_filter_limit = float(self.cfg.get("knn_max_area_ratio_for_filter", 0.02)) * image_area
        knn_suppressed_gate = int(knn_area > knn_gate_limit)
        knn_suppressed_filter = int(knn_area > knn_filter_limit)

        gate_knn = np.zeros_like(knn_mask) if knn_suppressed_gate else knn_mask
        gate_mask = cv2.bitwise_or(fd_mask, cv2.bitwise_or(mog_mask, gate_knn))
        gate_mask = morph(gate_mask)

        mog_clean, kept_components, removed_large, removed_bad_shape = precision_component_filter(
            mog_mask, self.cfg, image_area
        )
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fd_for_agreement = fd_mask.copy()
        fd_iters = int(self.cfg.get("dilate_fd_iterations", 1))
        if fd_iters > 0:
            fd_for_agreement = cv2.dilate(fd_for_agreement, dilate_kernel, iterations=fd_iters)
        agreement_mask = cv2.bitwise_and(fd_for_agreement, knn_mask)

        if knn_suppressed_filter:
            mog_for_agreement = mog_clean.copy()
            mog_iters = int(self.cfg.get("dilate_mog_iterations", 1))
            if mog_iters > 0:
                mog_for_agreement = cv2.dilate(mog_for_agreement, dilate_kernel, iterations=mog_iters)
            filter_seed = cv2.bitwise_and(fd_for_agreement, mog_for_agreement)
        else:
            filter_seed = cv2.bitwise_or(mog_clean, agreement_mask)

        filter_mask, kept_filter_components, removed_large_filter, removed_bad_shape_filter = precision_component_filter(
            filter_seed, self.cfg, image_area
        )
        if np.sum(filter_mask > 0) == 0 and np.sum(filter_seed > 0) > 0:
            filter_mask = filter_seed

        motion_area = int(np.sum(gate_mask > 0))
        min_area = max(20, int(image_area * float(self.cfg.get("min_area_ratio", 0.001))))
        motion_density = motion_area / float(image_area)
        area_score = min(1.0, motion_area / float(min_area * 6 + 1))
        illum_penalty = min(0.6, illum_diff / 80.0)
        temporal_persistence = 1.0 if self.state["last_detection_age"] < int(self.cfg.get("recent_object_memory", 30)) else 0.0
        gate_score = 0.45 * area_score + 0.20 * min(1.0, motion_density * 80) + 0.20 * temporal_persistence - 0.15 * illum_penalty
        gate_score = max(0.0, min(1.0, gate_score))

        open_t = float(self.cfg.get("open_threshold", 0.70))
        close_t = float(self.cfg.get("close_threshold", 0.45))
        if gate_score >= open_t:
            self.state["gate_open"] = True
        elif gate_score <= close_t:
            self.state["gate_open"] = False

        watchdog = False
        if not self.state["gate_open"]:
            self.state["closed_count"] += 1
            trigger = int(self.cfg.get("watchdog_closed_frames", 25))
            interval = int(self.cfg.get("watchdog_interval", 10))
            if self.state["closed_count"] >= trigger and self.state["closed_count"] % interval == 0:
                watchdog = True
        else:
            self.state["closed_count"] = 0

        gate_open = self.state["gate_open"] or watchdog
        self.last_debug_masks = {
            "fd_mask": fd_mask.copy(),
            "mog_mask": mog_mask.copy(),
            "knn_mask": knn_mask.copy(),
            "gate_mask_before_filter": gate_mask.copy(),
            "filter_mask_after_component": filter_mask.copy(),
        }
        info = {
            "gate_score": gate_score,
            "motion_area": motion_area,
            "motion_density": motion_density,
            "illumination_diff": illum_diff,
            "component_entropy_mean": 0.0,
            "kept_components": kept_filter_components,
            "watchdog_triggered": int(watchdog),
            "fd_area": fd_area,
            "mog_area": mog_area,
            "knn_area": knn_area,
            "mog_clean_area": int(np.sum(mog_clean > 0)),
            "agreement_area": int(np.sum(agreement_mask > 0)),
            "gate_area": int(np.sum(gate_mask > 0)),
            "filter_area": int(np.sum(filter_mask > 0)),
            "final_area": int(np.sum(filter_mask > 0)),
            "fusion_mode": self.cfg.get("fusion_mode", "mog2_plus_agreement"),
            "knn_suppressed_gate": knn_suppressed_gate,
            "knn_suppressed_filter": knn_suppressed_filter,
            "removed_large_components": removed_large + removed_large_filter,
            "removed_bad_shape_components": removed_bad_shape + removed_bad_shape_filter,
        }
        return gate_open, filter_mask, info

class ASMAGPlusEfficientGate(ASMAGPlusGate):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.efficient_state = {
            "gate_score_smooth": None,
            "open_streak": 0,
            "closed_streak": 0,
            "cooldown_remaining": 0,
            "eval_count": 0,
        }

    def process(self, frame, prev_frame=None, state=None):
        state = state or {}
        is_evaluation = bool(state.get("is_evaluation", True))
        evaluated_index = state.get("evaluated_index", self.efficient_state["eval_count"])
        previous_gate_state = self.state["gate_open"]
        gate_open_raw, filter_mask, info = super().process(frame, prev_frame, state)
        raw_score = float(info.get("gate_score", 0.0))
        beta = float(self.cfg.get("beta", 0.7))
        prev_smooth = self.efficient_state["gate_score_smooth"]
        smooth = raw_score if prev_smooth is None else beta * prev_smooth + (1.0 - beta) * raw_score
        self.efficient_state["gate_score_smooth"] = smooth

        open_t = float(self.cfg.get("open_threshold", 0.72))
        close_t = float(self.cfg.get("close_threshold", 0.45))
        force_close_t = float(self.cfg.get("force_close_threshold", 0.65))
        max_open_streak = int(self.cfg.get("max_open_streak", 15))
        cooldown_frames = int(self.cfg.get("cooldown_frames", 3))
        sample_interval = max(1, int(self.cfg.get("sample_interval", 10)))

        opened_by_score = 0
        opened_by_hysteresis = 0
        forced_close = 0
        cooldown_active = 0
        opened_by_periodic_sample = 0

        if self.efficient_state["cooldown_remaining"] > 0:
            gate_open = False
            cooldown_active = 1
            self.efficient_state["cooldown_remaining"] -= 1
        elif smooth >= open_t:
            gate_open = True
            opened_by_score = 1
        elif smooth <= close_t:
            gate_open = False
        else:
            gate_open = previous_gate_state
            opened_by_hysteresis = int(gate_open)

        if gate_open and self.efficient_state["open_streak"] >= max_open_streak and smooth < force_close_t:
            gate_open = False
            forced_close = 1
            self.efficient_state["cooldown_remaining"] = cooldown_frames

        if is_evaluation and not gate_open and int(evaluated_index) % sample_interval == 0:
            gate_open = True
            opened_by_periodic_sample = 1

        if gate_open:
            self.efficient_state["open_streak"] += 1
            self.efficient_state["closed_streak"] = 0
        else:
            self.efficient_state["closed_streak"] += 1
            self.efficient_state["open_streak"] = 0
        if is_evaluation:
            self.efficient_state["eval_count"] = int(evaluated_index) + 1
        self.state["gate_open"] = gate_open

        info.update({
            "gate_score_raw": raw_score,
            "gate_score_smooth": smooth,
            "opened_by_score": opened_by_score,
            "opened_by_hysteresis": opened_by_hysteresis,
            "forced_close": forced_close,
            "cooldown_active": cooldown_active,
            "opened_by_periodic_sample": opened_by_periodic_sample,
            "open_streak": self.efficient_state["open_streak"],
            "closed_streak": self.efficient_state["closed_streak"],
            "evaluated_index": evaluated_index if is_evaluation else "",
            "periodic_sample_basis": "evaluated_index",
        })
        return gate_open, filter_mask, info

    def reset_runtime_state(self):
        super().reset_runtime_state()
        self.efficient_state = {
            "gate_score_smooth": None,
            "open_streak": 0,
            "closed_streak": 0,
            "cooldown_remaining": 0,
            "eval_count": 0,
        }
