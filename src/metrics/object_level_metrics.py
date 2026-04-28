import numpy as np

from evaluation.mask_to_boxes import box_iou, match_boxes_by_iou


DEFAULT_IOU_THRESHOLDS = (0.3, 0.5, 0.75)
MAP_PROXY_THRESHOLDS = tuple(round(x, 2) for x in np.arange(0.5, 1.0, 0.05))


def area_normalized_scores(pred_boxes, image_shape=None):
    """Proxy confidence for mask-derived boxes when detector scores are unavailable."""
    if not pred_boxes:
        return []
    if image_shape is None:
        areas = [_box_area(box) for box in pred_boxes]
        max_area = max(areas) if areas else 0.0
        return [float(area / max_area) if max_area > 0 else 1.0 for area in areas]

    h, w = image_shape[:2]
    frame_area = float(max(1, h * w))
    return [float(min(1.0, max(0.0, _box_area(box) / frame_area))) for box in pred_boxes]


def assign_proxy_scores(pred_boxes, detector_boxes=None, detector_scores=None, image_shape=None):
    """
    Assign object confidence scores.

    This is a proxy metric for CDnet because CDnet mask ground truth does not provide
    per-object confidence. If YOLO scores are available, each mask-derived box receives
    the score of the best-overlapping YOLO box. Otherwise, an area-normalized proxy is
    used; if that cannot be computed, the fallback confidence is 1.0.
    """
    if not pred_boxes:
        return []

    detector_boxes = detector_boxes or []
    detector_scores = detector_scores or []
    if detector_boxes and detector_scores:
        scores = []
        for pred_box in pred_boxes:
            best_score = None
            best_iou = 0.0
            for det_box, det_score in zip(detector_boxes, detector_scores):
                iou = box_iou(pred_box, det_box)
                if iou > best_iou:
                    best_iou = iou
                    best_score = float(det_score)
            scores.append(best_score if best_score is not None and best_iou > 0 else 1.0)
        return scores

    scores = area_normalized_scores(pred_boxes, image_shape)
    return scores if scores else [1.0] * len(pred_boxes)


def object_counts_at_threshold(pred_boxes, gt_boxes, iou_threshold):
    matches, unmatched_pred, unmatched_gt = match_boxes_by_iou(pred_boxes, gt_boxes, iou_threshold)
    return {
        "TP_object": len(matches),
        "FP_object": len(unmatched_pred),
        "FN_object": len(unmatched_gt),
        "matched_ious": [m["iou"] for m in matches],
    }


def average_precision_proxy(records, iou_threshold=0.5):
    """
    Compute AP using detector/proxy confidence scores.

    This is a proxy AP for CDnet mask evaluation, not COCO/VOC detector AP from
    annotated object confidence labels.
    """
    total_gt = sum(len(record.get("gt_boxes", [])) for record in records)
    detections = []
    gt_matched = {}

    for frame_idx, record in enumerate(records):
        for pred_idx, (box, score) in enumerate(zip(record.get("pred_boxes", []), record.get("scores", []))):
            detections.append((float(score), frame_idx, pred_idx, box))
        gt_matched[frame_idx] = set()

    if total_gt == 0:
        return 0.0
    if not detections:
        return 0.0

    detections.sort(key=lambda item: item[0], reverse=True)
    tp = np.zeros(len(detections), dtype=np.float64)
    fp = np.zeros(len(detections), dtype=np.float64)

    for det_idx, (_, frame_idx, _, pred_box) in enumerate(detections):
        gt_boxes = records[frame_idx].get("gt_boxes", [])
        best_iou = 0.0
        best_gt_idx = None
        for gt_idx, gt_box in enumerate(gt_boxes):
            if gt_idx in gt_matched[frame_idx]:
                continue
            iou = box_iou(pred_box, gt_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx
        if best_gt_idx is not None and best_iou >= iou_threshold:
            tp[det_idx] = 1.0
            gt_matched[frame_idx].add(best_gt_idx)
        else:
            fp[det_idx] = 1.0

    cum_tp = np.cumsum(tp)
    cum_fp = np.cumsum(fp)
    recall = cum_tp / total_gt
    precision = cum_tp / np.maximum(cum_tp + cum_fp, 1e-12)
    return _integral_ap(recall, precision)


def summarize_object_records(records, iou_thresholds=None):
    iou_thresholds = tuple(
        sorted(set(iou_thresholds or (DEFAULT_IOU_THRESHOLDS + MAP_PROXY_THRESHOLDS)))
    )
    summary = {
        "object_frame_count": len(records),
        "pred_object_count": int(sum(len(r.get("pred_boxes", [])) for r in records)),
        "gt_object_count": int(sum(len(r.get("gt_boxes", [])) for r in records)),
        "score_source": _score_source_summary(records),
    }

    for threshold in iou_thresholds:
        counts = _aggregate_counts(records, threshold)
        suffix = _threshold_suffix(threshold)
        summary[f"TP_object_{suffix}"] = counts["TP_object"]
        summary[f"FP_object_{suffix}"] = counts["FP_object"]
        summary[f"FN_object_{suffix}"] = counts["FN_object"]
        summary[f"Object_Precision_{suffix}"] = counts["precision"]
        summary[f"Object_Recall_{suffix}"] = counts["recall"]
        summary[f"Object_F1_{suffix}"] = counts["f1"]
        summary[f"Mean_IoU_{suffix}"] = counts["mean_iou"]
        summary[f"AP_{suffix}_proxy"] = average_precision_proxy(records, threshold)

    counts_50 = _aggregate_counts(records, 0.5)
    summary.update(
        {
            "TP_object": counts_50["TP_object"],
            "FP_object": counts_50["FP_object"],
            "FN_object": counts_50["FN_object"],
            "Object_Precision": counts_50["precision"],
            "Object_Recall": counts_50["recall"],
            "Object_F1": counts_50["f1"],
            "Mean_IoU": counts_50["mean_iou"],
            "AP": average_precision_proxy(records, 0.5),
            "mAP_50": average_precision_proxy(records, 0.5),
            "mAP_50_95_proxy": float(np.mean([average_precision_proxy(records, t) for t in MAP_PROXY_THRESHOLDS])),
        }
    )
    return summary


def build_object_group_summary(object_rows, group_cols):
    if not object_rows:
        return []
    groups = {}
    for row in object_rows:
        key = tuple(row.get(col, "") for col in group_cols)
        groups.setdefault(key, []).append(row)

    summaries = []
    for key, rows in groups.items():
        summary = {col: value for col, value in zip(group_cols, key)}
        for threshold in DEFAULT_IOU_THRESHOLDS:
            suffix = _threshold_suffix(threshold)
            tp = int(sum(r.get(f"TP_object_{suffix}", 0) for r in rows))
            fp = int(sum(r.get(f"FP_object_{suffix}", 0) for r in rows))
            fn = int(sum(r.get(f"FN_object_{suffix}", 0) for r in rows))
            precision, recall, f1 = _prf(tp, fp, fn)
            summary[f"TP_object_{suffix}"] = tp
            summary[f"FP_object_{suffix}"] = fp
            summary[f"FN_object_{suffix}"] = fn
            summary[f"Object_Precision_{suffix}"] = precision
            summary[f"Object_Recall_{suffix}"] = recall
            summary[f"Object_F1_{suffix}"] = f1

        tp = int(sum(r.get("TP_object", 0) for r in rows))
        fp = int(sum(r.get("FP_object", 0) for r in rows))
        fn = int(sum(r.get("FN_object", 0) for r in rows))
        precision, recall, f1 = _prf(tp, fp, fn)
        summary.update(
            {
                "TP_object": tp,
                "FP_object": fp,
                "FN_object": fn,
                "Object_Precision": precision,
                "Object_Recall": recall,
                "Object_F1": f1,
                "Mean_IoU": _weighted_mean(rows, "Mean_IoU", "TP_object"),
                "AP": float(np.mean([r.get("AP", 0.0) for r in rows])),
                "mAP_50": float(np.mean([r.get("mAP_50", 0.0) for r in rows])),
                "mAP_50_95_proxy": float(np.mean([r.get("mAP_50_95_proxy", 0.0) for r in rows])),
                "object_frame_count": int(sum(r.get("object_frame_count", 0) for r in rows)),
                "pred_object_count": int(sum(r.get("pred_object_count", 0) for r in rows)),
                "gt_object_count": int(sum(r.get("gt_object_count", 0) for r in rows)),
            }
        )
        summaries.append(summary)
    return summaries


def _aggregate_counts(records, iou_threshold):
    tp = fp = fn = 0
    matched_ious = []
    for record in records:
        counts = object_counts_at_threshold(
            record.get("pred_boxes", []),
            record.get("gt_boxes", []),
            iou_threshold,
        )
        tp += counts["TP_object"]
        fp += counts["FP_object"]
        fn += counts["FN_object"]
        matched_ious.extend(counts["matched_ious"])
    precision, recall, f1 = _prf(tp, fp, fn)
    return {
        "TP_object": tp,
        "FP_object": fp,
        "FN_object": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_iou": float(np.mean(matched_ious)) if matched_ious else 0.0,
    }


def _integral_ap(recall, precision):
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([0.0], precision, [0.0]))
    for idx in range(len(mpre) - 2, -1, -1):
        mpre[idx] = max(mpre[idx], mpre[idx + 1])
    changing = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[changing + 1] - mrec[changing]) * mpre[changing + 1]))


def _box_area(box):
    return max(0.0, float(box[2]) - float(box[0])) * max(0.0, float(box[3]) - float(box[1]))


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def _score_source_summary(records):
    sources = sorted({r.get("score_source", "unknown") for r in records})
    return "+".join(sources) if sources else "none"


def _threshold_suffix(threshold):
    return f"iou_{str(threshold).replace('.', '_')}"


def _weighted_mean(rows, value_col, weight_col):
    weighted_sum = sum(float(r.get(value_col, 0.0)) * float(r.get(weight_col, 0.0)) for r in rows)
    weight_sum = sum(float(r.get(weight_col, 0.0)) for r in rows)
    return weighted_sum / weight_sum if weight_sum > 0 else 0.0
