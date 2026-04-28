import math
import numpy as np

from metrics.cdnet_pixel_metrics import (
    aggregate_pixel as aggregate_cdnet_pixel,
    pixel_metrics as cdnet_pixel_metrics,
    valid_gt_mask as cdnet_valid_gt_mask,
)

def valid_gt_mask(gt, cdnet_gt_config=None):
    return cdnet_valid_gt_mask(gt, cdnet_gt_config)

def pixel_metrics(pred_mask, gt, cdnet_gt_config=None):
    return cdnet_pixel_metrics(pred_mask, gt, cdnet_gt_config)

def event_state_from_masks(pred_alert, gt, cdnet_gt_config=None):
    fg, _, _ = valid_gt_mask(gt, cdnet_gt_config)
    active = bool(np.any(fg))
    if active and pred_alert: return "TP", 1
    if (not active) and (not pred_alert): return "TN", 0
    if (not active) and pred_alert: return "FP", 0
    return "FN", 1

def summarize_event(df):
    e_tp = int((df.Event_State=="TP").sum())
    e_tn = int((df.Event_State=="TN").sum())
    e_fp = int((df.Event_State=="FP").sum())
    e_fn = int((df.Event_State=="FN").sum())
    total = e_tp+e_tn+e_fp+e_fn
    acc = (e_tp+e_tn)/total if total else 0
    prec = e_tp/(e_tp+e_fp) if (e_tp+e_fp)>0 else 0
    rec = e_tp/(e_tp+e_fn) if (e_tp+e_fn)>0 else 0
    f1 = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0
    den = math.sqrt((e_tp+e_fp)*(e_tp+e_fn)*(e_tn+e_fp)*(e_tn+e_fn))
    mcc = ((e_tp*e_tn)-(e_fp*e_fn))/den if den else 0
    return dict(Event_TP=e_tp,Event_TN=e_tn,Event_FP=e_fp,Event_FN=e_fn,Event_Accuracy=acc,Event_Precision=prec,Event_Recall=rec,Event_F1=f1,MCC=mcc)

def aggregate_pixel(rows):
    return aggregate_cdnet_pixel(rows)
