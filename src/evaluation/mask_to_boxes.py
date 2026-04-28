import cv2
import numpy as np


def mask_to_connected_components(mask, min_area=20):
    """Return connected foreground components from a binary-like mask."""
    if mask is None:
        return []
    if mask.ndim == 3:
        mask = mask[:, :, 0]
    binary = (mask > 0).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    components = []
    for label in range(1, num_labels):
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w = int(stats[label, cv2.CC_STAT_WIDTH])
        h = int(stats[label, cv2.CC_STAT_HEIGHT])
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        components.append(
            {
                "label": label,
                "box": [x, y, x + w, y + h],
                "area": area,
                "mask": labels == label,
            }
        )
    return components


def mask_to_boxes(mask, min_area=20):
    """Convert connected foreground components to [x1, y1, x2, y2] boxes."""
    return [component["box"] for component in mask_to_connected_components(mask, min_area)]


def box_iou(boxA, boxB):
    xA = max(float(boxA[0]), float(boxB[0]))
    yA = max(float(boxA[1]), float(boxB[1]))
    xB = min(float(boxA[2]), float(boxB[2]))
    yB = min(float(boxA[3]), float(boxB[3]))

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    areaA = max(0.0, float(boxA[2]) - float(boxA[0])) * max(0.0, float(boxA[3]) - float(boxA[1]))
    areaB = max(0.0, float(boxB[2]) - float(boxB[0])) * max(0.0, float(boxB[3]) - float(boxB[1]))
    union = areaA + areaB - inter_area
    return inter_area / union if union > 0 else 0.0


def match_boxes_by_iou(pred_boxes, gt_boxes, iou_threshold):
    """Greedily match predicted boxes to GT boxes by descending IoU."""
    candidates = []
    for pred_idx, pred_box in enumerate(pred_boxes):
        for gt_idx, gt_box in enumerate(gt_boxes):
            iou = box_iou(pred_box, gt_box)
            if iou >= iou_threshold:
                candidates.append((iou, pred_idx, gt_idx))

    matches = []
    used_pred, used_gt = set(), set()
    for iou, pred_idx, gt_idx in sorted(candidates, reverse=True):
        if pred_idx in used_pred or gt_idx in used_gt:
            continue
        used_pred.add(pred_idx)
        used_gt.add(gt_idx)
        matches.append({"pred_idx": pred_idx, "gt_idx": gt_idx, "iou": float(iou)})

    unmatched_pred = [i for i in range(len(pred_boxes)) if i not in used_pred]
    unmatched_gt = [i for i in range(len(gt_boxes)) if i not in used_gt]
    return matches, unmatched_pred, unmatched_gt
