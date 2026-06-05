#!/usr/bin/env python3
"""
Jetson Orin Nano Hardware Profiler for ASMAG Pipelines
Measures: FPS, per-frame latency, power draw (via tegrastats)
Pipelines: P1_YOLO_Only, P3_MOG2, GUARDED (MOG2-gated YOLO)
"""
import os, sys, time, csv, threading, subprocess, re, warnings
import numpy as np
import cv2
warnings.filterwarnings("ignore")

VIDEOS_ROOT = os.path.expanduser("~/cdnet2014")
MODEL_PATH  = os.path.expanduser("~/models/yolo26s.pt")
OUTPUT_DIR  = os.path.expanduser("~/profiling_results")
WARMUP      = 10
MOTION_THR  = 0.02   # fraction of frame pixels to trigger GUARDED gate
PIPELINES   = ["P1_YOLO_Only", "P3_MOG2", "GUARDED"]

# ------------------------------------------------------------------ #
#  Power logger via tegrastats
# ------------------------------------------------------------------ #
class TegrastatsLogger:
    def __init__(self, interval_ms=500):
        self.interval_ms = interval_ms
        self.readings_mw = []
        self._running = False
        self._proc  = None
        self._thread = None

    def start(self):
        self.readings_mw = []
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        time.sleep(0.7)

    def stop(self):
        self._running = False
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self):
        try:
            self._proc = subprocess.Popen(
                ["/usr/bin/tegrastats", "--interval", str(self.interval_ms)],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
            )
            while self._running:
                line = self._proc.stdout.readline()
                if not line:
                    break
                mw = self._parse(line)
                if mw is not None:
                    self.readings_mw.append(mw)
        except Exception:
            pass

    def _parse(self, line):
        # JP6 format: VDD_IN 2345mW/3000mW  or  VDD_IN 2345/3000
        m = re.search(r"VDD_IN\s+(\d+)", line)
        return int(m.group(1)) if m else None

    def avg_mw(self):
        return float(np.mean(self.readings_mw)) if self.readings_mw else 0.0

    def p90_mw(self):
        return float(np.percentile(self.readings_mw, 90)) if self.readings_mw else 0.0


def _read_ina3221_mw():
    """Sysfs fallback power reading for VDD_IN (rail index 1 on JP6 hwmon1)."""
    try:
        base = "/sys/class/hwmon/hwmon1"
        v_mv = int(open(f"{base}/in1_input").read())
        i_ma = int(open(f"{base}/curr1_input").read())
        return v_mv * i_ma / 1e6  # mW
    except Exception:
        return None


# ------------------------------------------------------------------ #
#  Pipeline runners
# ------------------------------------------------------------------ #

def run_p1_yolo(frames_dir, model):
    import torch
    files = sorted(
        f for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )
    lat, logger = [], TegrastatsLogger()
    logger.start()
    for i, fn in enumerate(files):
        frame = cv2.imread(os.path.join(frames_dir, fn))
        if frame is None:
            continue
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = model(frame, verbose=False, device="cpu")
        t1 = time.perf_counter()
        if i >= WARMUP:
            lat.append((t1 - t0) * 1000)
    logger.stop()
    if not lat:
        return {}
    return dict(
        n=len(lat), fps=1000.0 / np.mean(lat),
        lat_avg=float(np.mean(lat)), lat_p90=float(np.percentile(lat, 90)),
        act=1.0, pwr=logger.avg_mw(), pwr_p90=logger.p90_mw()
    )


def run_p3_mog2(frames_dir):
    files = sorted(
        f for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )
    bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=16, detectShadows=True)
    lat, logger = [], TegrastatsLogger()
    logger.start()
    for i, fn in enumerate(files):
        frame = cv2.imread(os.path.join(frames_dir, fn))
        if frame is None:
            continue
        t0 = time.perf_counter()
        _ = bg.apply(frame)
        t1 = time.perf_counter()
        if i >= WARMUP:
            lat.append((t1 - t0) * 1000)
    logger.stop()
    if not lat:
        return {}
    return dict(
        n=len(lat), fps=1000.0 / np.mean(lat),
        lat_avg=float(np.mean(lat)), lat_p90=float(np.percentile(lat, 90)),
        act=0.0, pwr=logger.avg_mw(), pwr_p90=logger.p90_mw()
    )


def run_guarded(frames_dir, model):
    import torch
    files = sorted(
        f for f in os.listdir(frames_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )
    bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=16, detectShadows=True)
    lat, yolo_calls, logger = [], 0, TegrastatsLogger()
    logger.start()
    for i, fn in enumerate(files):
        frame = cv2.imread(os.path.join(frames_dir, fn))
        if frame is None:
            continue
        t0 = time.perf_counter()
        mask  = bg.apply(frame)
        ratio = np.count_nonzero(mask > 127) / mask.size
        if ratio > MOTION_THR:
            with torch.no_grad():
                _ = model(frame, verbose=False, device="cpu")
            if i >= WARMUP:
                yolo_calls += 1
        t1 = time.perf_counter()
        if i >= WARMUP:
            lat.append((t1 - t0) * 1000)
    logger.stop()
    if not lat:
        return {}
    act = yolo_calls / len(lat) if lat else 0.0
    return dict(
        n=len(lat), fps=1000.0 / np.mean(lat),
        lat_avg=float(np.mean(lat)), lat_p90=float(np.percentile(lat, 90)),
        act=act, pwr=logger.avg_mw(), pwr_p90=logger.p90_mw()
    )


# ------------------------------------------------------------------ #
#  Main
# ------------------------------------------------------------------ #

def find_input_dir(vdir):
    for d in ("input", "Input", "frames", "RGB"):
        p = os.path.join(vdir, d)
        if os.path.isdir(p):
            return p
    return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tg_ok = os.path.exists("/usr/bin/tegrastats")
    print(f"tegrastats available: {tg_ok}")
    if not tg_ok:
        pw = _read_ina3221_mw()
        print(f"ina3221 sysfs fallback: {pw} mW")

    from ultralytics import YOLO
    import torch
    print(f"torch {torch.__version__}  CUDA:{torch.cuda.is_available()}")
    model = YOLO(MODEL_PATH)
    print(f"Model loaded: {MODEL_PATH}")

    # Collect all videos
    videos = []
    for cat in sorted(os.listdir(VIDEOS_ROOT)):
        cat_dir = os.path.join(VIDEOS_ROOT, cat)
        if not os.path.isdir(cat_dir):
            continue
        for vid in sorted(os.listdir(cat_dir)):
            vdir = os.path.join(cat_dir, vid)
            if not os.path.isdir(vdir):
                continue
            idir = find_input_dir(vdir)
            if idir:
                videos.append((cat, vid, idir))

    print(f"Videos found: {len(videos)}")

    FIELDS = [
        "category", "video", "pipeline", "n_frames", "fps",
        "avg_latency_ms", "p90_latency_ms", "activation_rate",
        "avg_power_mw", "p90_power_mw"
    ]
    rows = []

    for cat, vid, idir in videos:
        nf = len([f for f in os.listdir(idir) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
        print(f"\n--- {cat}/{vid}  ({nf} frames) ---")

        for pipe in PIPELINES:
            print(f"  {pipe} ... ", end="", flush=True)
            try:
                if pipe == "P1_YOLO_Only":
                    m = run_p1_yolo(idir, model)
                elif pipe == "P3_MOG2":
                    m = run_p3_mog2(idir)
                else:
                    m = run_guarded(idir, model)

                row = {
                    "category": cat, "video": vid, "pipeline": pipe,
                    "n_frames": m.get("n", 0),
                    "fps": round(m.get("fps", 0), 3),
                    "avg_latency_ms": round(m.get("lat_avg", 0), 2),
                    "p90_latency_ms": round(m.get("lat_p90", 0), 2),
                    "activation_rate": round(m.get("act", 0), 4),
                    "avg_power_mw": round(m.get("pwr", 0), 1),
                    "p90_power_mw": round(m.get("pwr_p90", 0), 1),
                }
                rows.append(row)
                print(
                    f"fps={row['fps']:.1f}  lat={row['avg_latency_ms']:.1f}ms  "
                    f"act={row['activation_rate']:.2f}  pwr={row['avg_power_mw']:.0f}mW"
                )
            except Exception as e:
                print(f"ERROR: {e}")
                rows.append({"category": cat, "video": vid, "pipeline": pipe,
                             **{k: 0 for k in FIELDS[3:]}})

    out = os.path.join(OUTPUT_DIR, "jetson_profiling_results.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved: {out}")

    # Summary table
    print("\n========== SUMMARY ==========")
    by_pipe = {}
    for r in rows:
        by_pipe.setdefault(r["pipeline"], []).append(r)

    for p, rs in by_pipe.items():
        fps_v = [r["fps"] for r in rs if r["fps"] > 0]
        lat_v = [r["avg_latency_ms"] for r in rs if r["avg_latency_ms"] > 0]
        pwr_v = [r["avg_power_mw"] for r in rs if r["avg_power_mw"] > 0]
        act_v = [r["activation_rate"] for r in rs]
        print(f"\n{p}:")
        if fps_v:
            print(f"  FPS     : {np.mean(fps_v):.2f} avg  range [{min(fps_v):.2f}, {max(fps_v):.2f}]")
        if lat_v:
            print(f"  Latency : {np.mean(lat_v):.1f}ms avg  p90={np.percentile(lat_v, 90):.1f}ms")
        if pwr_v:
            print(f"  Power   : {np.mean(pwr_v):.0f}mW avg")
        if act_v:
            print(f"  Act rate: {np.mean(act_v):.3f}")


if __name__ == "__main__":
    main()
