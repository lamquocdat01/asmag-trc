#!/usr/bin/env python3
"""
Jetson Orin Nano TensorRT Profiling for ASMAG-TRC paper.
Exports YOLO26s to TensorRT FP16 and FP32, then profiles:
  - P1_YOLO_Only (TensorRT FP16)
  - P1_YOLO_Only (TensorRT FP32)
  - P1_YOLO_Only (PyTorch FP32) — baseline from previous run
  - P3_MOG2
  - ONLINE_GUARDED (TensorRT FP16)
  - ONLINE_GUARDED (TensorRT FP32)
  - ONLINE_GUARDED (PyTorch FP32) — baseline
Measures: FPS, latency, power (VDD_IN, CPU_GPU_CV, SOC), energy/frame, GPU memory
"""
import os, sys, time, csv, threading, subprocess, re, warnings
import numpy as np
import cv2
warnings.filterwarnings("ignore")
import torch
from ultralytics import YOLO

# === CONFIGURATION ===
MODEL_PT = "/models/yolo26s.pt"
MODEL_TRT_FP16 = "/models/yolo26s_fp16.engine"
MODEL_TRT_FP32 = "/models/yolo26s_fp32.engine"
VIDEOS_ROOT = "/cdnet2014"
OUTPUT_DIR = "/output"
WARMUP = 20
MOTION_THR = 0.02
FRAMES_PER_VIDEO = 500  # more frames for better measurement

print(f"torch {torch.__version__} CUDA:{torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB")

# === STEP 1: Export to TensorRT ===
print("\n" + "="*60)
print("STEP 1: Export YOLO26s to TensorRT engines")
print("="*60)

model_pt = YOLO(MODEL_PT)

# Export FP16
if not os.path.exists(MODEL_TRT_FP16):
    print("\nExporting FP16 TensorRT engine... (may take 5-10 minutes)")
    try:
        model_pt.export(format="engine", half=True, device=0, imgsz=640)
        # ultralytics saves engine next to .pt file
        exported = MODEL_PT.replace(".pt", ".engine")
        if os.path.exists(exported):
            os.rename(exported, MODEL_TRT_FP16)
            print(f"FP16 engine saved: {MODEL_TRT_FP16} ({os.path.getsize(MODEL_TRT_FP16)/1024/1024:.1f} MB)")
        else:
            # Try alternative naming
            alt_paths = [
                MODEL_PT.replace(".pt", "_fp16.engine"),
                "/models/yolo26s.engine",
            ]
            for alt in alt_paths:
                if os.path.exists(alt):
                    os.rename(alt, MODEL_TRT_FP16)
                    print(f"FP16 engine found at {alt}, moved to {MODEL_TRT_FP16}")
                    break
            else:
                print("WARNING: FP16 export completed but engine file not found at expected path")
                # List /models/ to find it
                print("Files in /models/:", os.listdir("/models/"))
    except Exception as e:
        print(f"FP16 export failed: {e}")
        print("Continuing with FP32 only...")
else:
    print(f"FP16 engine already exists: {MODEL_TRT_FP16}")

# Export FP32
if not os.path.exists(MODEL_TRT_FP32):
    print("\nExporting FP32 TensorRT engine...")
    try:
        model_pt2 = YOLO(MODEL_PT)
        model_pt2.export(format="engine", half=False, device=0, imgsz=640)
        exported = MODEL_PT.replace(".pt", ".engine")
        if os.path.exists(exported):
            os.rename(exported, MODEL_TRT_FP32)
            print(f"FP32 engine saved: {MODEL_TRT_FP32} ({os.path.getsize(MODEL_TRT_FP32)/1024/1024:.1f} MB)")
        else:
            for f in os.listdir("/models/"):
                if f.endswith(".engine") and f != os.path.basename(MODEL_TRT_FP16):
                    src = os.path.join("/models/", f)
                    os.rename(src, MODEL_TRT_FP32)
                    print(f"FP32 engine: {src} -> {MODEL_TRT_FP32}")
                    break
    except Exception as e:
        print(f"FP32 export failed: {e}")
else:
    print(f"FP32 engine already exists: {MODEL_TRT_FP32}")

# === STEP 2: Load models ===
print("\n" + "="*60)
print("STEP 2: Load all model variants")
print("="*60)

models = {}

# PyTorch FP32
models["PyTorch_FP32"] = {"model": YOLO(MODEL_PT), "device": "cuda:0"}
print("Loaded PyTorch FP32")

# TensorRT FP16
if os.path.exists(MODEL_TRT_FP16):
    try:
        models["TensorRT_FP16"] = {"model": YOLO(MODEL_TRT_FP16), "device": 0}
        print("Loaded TensorRT FP16")
    except Exception as e:
        print(f"TensorRT FP16 load failed: {e}")

# TensorRT FP32
if os.path.exists(MODEL_TRT_FP32):
    try:
        models["TensorRT_FP32"] = {"model": YOLO(MODEL_TRT_FP32), "device": 0}
        print("Loaded TensorRT FP32")
    except Exception as e:
        print(f"TensorRT FP32 load failed: {e}")

print(f"\nLoaded {len(models)} model variants: {list(models.keys())}")

# Warmup all models
dummy = np.zeros((480, 640, 3), dtype=np.uint8)
for name, m in models.items():
    print(f"Warming up {name}...", end=" ", flush=True)
    for _ in range(WARMUP):
        m["model"](dummy, verbose=False, device=m["device"])
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    print("done")

# === TEGRASTATS LOGGER ===
class TegrastatsLogger:
    def __init__(self):
        self.power_vdd_in = []
        self.power_cpu_gpu = []
        self.power_soc = []
        self._running = False
    def start(self):
        self.power_vdd_in = []
        self.power_cpu_gpu = []
        self.power_soc = []
        self._running = True
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        time.sleep(0.7)
    def stop(self):
        self._running = False
        if hasattr(self, "_p"):
            try: self._p.terminate()
            except: pass
        self._t.join(timeout=3)
    def _run(self):
        if os.path.exists("/usr/bin/tegrastats"):
            try:
                self._p = subprocess.Popen(
                    ["/usr/bin/tegrastats", "--interval", "500"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                while self._running:
                    line = self._p.stdout.readline()
                    if not line: break
                    m = re.search(r"VDD_IN\s+(\d+)", line)
                    if m: self.power_vdd_in.append(int(m.group(1)))
                    m2 = re.search(r"VDD_CPU_GPU_CV\s+(\d+)", line)
                    if m2: self.power_cpu_gpu.append(int(m2.group(1)))
                    m3 = re.search(r"VDD_SOC\s+(\d+)", line)
                    if m3: self.power_soc.append(int(m3.group(1)))
                return
            except Exception: pass
        # INA3221 sysfs fallback (works in-container with -v /sys:/sys:ro; tegrastats absent there)
        H = "/sys/class/hwmon/hwmon1"
        while self._running:
            try:
                self.power_vdd_in.append(int(open(f"{H}/in1_input").read()) * int(open(f"{H}/curr1_input").read()) // 1000)
                self.power_cpu_gpu.append(int(open(f"{H}/in2_input").read()) * int(open(f"{H}/curr2_input").read()) // 1000)
                self.power_soc.append(int(open(f"{H}/in3_input").read()) * int(open(f"{H}/curr3_input").read()) // 1000)
            except Exception: pass
            time.sleep(0.5)
    def summary(self):
        def sm(lst): return float(np.mean(lst)) if lst else 0
        def sp(lst): return float(np.percentile(lst, 90)) if lst else 0
        return {
            "vdd_in_avg": round(sm(self.power_vdd_in), 1),
            "vdd_in_p90": round(sp(self.power_vdd_in), 1),
            "cpu_gpu_avg": round(sm(self.power_cpu_gpu), 1),
            "soc_avg": round(sm(self.power_soc), 1),
        }

# === STEP 3: Collect videos ===
# Optional filter: E6_TRT_VIDEOS="cat/video,cat/video" (empty = all). E6_TRT_FRAMES overrides count.
_VFILT = [v.strip() for v in os.environ.get("E6_TRT_VIDEOS", "").split(",") if v.strip()]
FRAMES_PER_VIDEO = int(os.environ.get("E6_TRT_FRAMES", str(FRAMES_PER_VIDEO)))
videos = []
for cat in sorted(os.listdir(VIDEOS_ROOT)):
    cd = os.path.join(VIDEOS_ROOT, cat)
    if not os.path.isdir(cd): continue
    for vid in sorted(os.listdir(cd)):
        vd = os.path.join(cd, vid)
        inp = os.path.join(vd, "input")
        if os.path.isdir(inp) and (not _VFILT or f"{cat}/{vid}" in _VFILT):
            videos.append((cat, vid, inp))
print(f"\nVideos: {len(videos)} | frames/video: {FRAMES_PER_VIDEO}")

# === STEP 4: Run profiling ===
print("\n" + "="*60)
print("STEP 3: Profiling all combinations")
print("="*60)

FIELDS = [
    "category", "video", "pipeline", "model_variant", "n_frames",
    "fps", "avg_latency_ms", "p90_latency_ms", "max_latency_ms",
    "activation_rate",
    "vdd_in_avg_mw", "vdd_in_p90_mw", "cpu_gpu_avg_mw", "soc_avg_mw",
    "energy_per_frame_mj", "gpu_mem_peak_mb",
]
rows = []

for cat, vid, idir in videos:
    files = sorted(f for f in os.listdir(idir) if f.endswith((".jpg", ".png")))[:FRAMES_PER_VIDEO]
    print(f"\n--- {cat}/{vid} ({len(files)} frames) ---")

    # For each model variant
    for model_name, model_info in models.items():
        model = model_info["model"]
        device = model_info["device"]

        # Run P1_YOLO_Only
        pipeline = f"P1_YOLO_{model_name}"
        print(f"  {pipeline} ... ", end="", flush=True)

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()

        bg = None
        lat, yolo_n = [], 0
        tg = TegrastatsLogger()
        tg.start()

        for i, fn in enumerate(files):
            frame = cv2.imread(os.path.join(idir, fn))
            if frame is None: continue
            if torch.cuda.is_available(): torch.cuda.synchronize()
            t0 = time.perf_counter()
            with torch.no_grad():
                model(frame, verbose=False, device=device)
            if torch.cuda.is_available(): torch.cuda.synchronize()
            if i >= WARMUP:
                lat.append((time.perf_counter() - t0) * 1000)
                yolo_n += 1

        tg.stop()
        if lat:
            n = len(lat)
            fps = 1000 / np.mean(lat)
            hw = tg.summary()
            gpu_mem = torch.cuda.max_memory_allocated() / 1024**2 if torch.cuda.is_available() else 0
            row = dict(category=cat, video=vid, pipeline="P1_YOLO_Only", model_variant=model_name,
                       n_frames=n, fps=round(fps, 2),
                       avg_latency_ms=round(np.mean(lat), 2),
                       p90_latency_ms=round(float(np.percentile(lat, 90)), 2),
                       max_latency_ms=round(float(np.max(lat)), 2),
                       activation_rate=1.0,
                       vdd_in_avg_mw=hw["vdd_in_avg"], vdd_in_p90_mw=hw["vdd_in_p90"],
                       cpu_gpu_avg_mw=hw["cpu_gpu_avg"], soc_avg_mw=hw["soc_avg"],
                       energy_per_frame_mj=round(hw["vdd_in_avg"] / fps, 2) if fps > 0 else 0,
                       gpu_mem_peak_mb=round(gpu_mem, 1))
            rows.append(row)
            print(f"fps={fps:.1f} lat={np.mean(lat):.1f}ms pwr={hw['vdd_in_avg']:.0f}mW E={hw['vdd_in_avg']/fps:.0f}mJ")

        # Run GUARDED
        pipeline = f"GUARDED_{model_name}"
        print(f"  {pipeline} ... ", end="", flush=True)

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()

        bg = cv2.createBackgroundSubtractorMOG2(200, 16, True)
        lat, yolo_n = [], 0
        tg = TegrastatsLogger()
        tg.start()

        for i, fn in enumerate(files):
            frame = cv2.imread(os.path.join(idir, fn))
            if frame is None: continue
            if torch.cuda.is_available(): torch.cuda.synchronize()
            t0 = time.perf_counter()
            mask = bg.apply(frame)
            ratio = np.count_nonzero(mask > 127) / mask.size
            if ratio > MOTION_THR:
                with torch.no_grad():
                    model(frame, verbose=False, device=device)
                if i >= WARMUP: yolo_n += 1
            if torch.cuda.is_available(): torch.cuda.synchronize()
            if i >= WARMUP:
                lat.append((time.perf_counter() - t0) * 1000)

        tg.stop()
        if lat:
            n = len(lat)
            act = yolo_n / n if n > 0 else 0
            fps = 1000 / np.mean(lat)
            hw = tg.summary()
            gpu_mem = torch.cuda.max_memory_allocated() / 1024**2 if torch.cuda.is_available() else 0
            row = dict(category=cat, video=vid, pipeline="ONLINE_GUARDED", model_variant=model_name,
                       n_frames=n, fps=round(fps, 2),
                       avg_latency_ms=round(np.mean(lat), 2),
                       p90_latency_ms=round(float(np.percentile(lat, 90)), 2),
                       max_latency_ms=round(float(np.max(lat)), 2),
                       activation_rate=round(act, 4),
                       vdd_in_avg_mw=hw["vdd_in_avg"], vdd_in_p90_mw=hw["vdd_in_p90"],
                       cpu_gpu_avg_mw=hw["cpu_gpu_avg"], soc_avg_mw=hw["soc_avg"],
                       energy_per_frame_mj=round(hw["vdd_in_avg"] / fps, 2) if fps > 0 else 0,
                       gpu_mem_peak_mb=round(gpu_mem, 1))
            rows.append(row)
            print(f"fps={fps:.1f} act={act:.2f} pwr={hw['vdd_in_avg']:.0f}mW E={hw['vdd_in_avg']/fps:.0f}mJ")

    # Also run P3_MOG2 once (no model variant needed)
    print(f"  P3_MOG2 ... ", end="", flush=True)
    bg = cv2.createBackgroundSubtractorMOG2(200, 16, True)
    lat = []
    tg = TegrastatsLogger()
    tg.start()
    for i, fn in enumerate(files):
        frame = cv2.imread(os.path.join(idir, fn))
        if frame is None: continue
        t0 = time.perf_counter()
        bg.apply(frame)
        if i >= WARMUP:
            lat.append((time.perf_counter() - t0) * 1000)
    tg.stop()
    if lat:
        n = len(lat)
        fps = 1000 / np.mean(lat)
        hw = tg.summary()
        row = dict(category=cat, video=vid, pipeline="P3_MOG2", model_variant="None",
                   n_frames=n, fps=round(fps, 2),
                   avg_latency_ms=round(np.mean(lat), 2),
                   p90_latency_ms=round(float(np.percentile(lat, 90)), 2),
                   max_latency_ms=round(float(np.max(lat)), 2),
                   activation_rate=0.0,
                   vdd_in_avg_mw=hw["vdd_in_avg"], vdd_in_p90_mw=hw["vdd_in_p90"],
                   cpu_gpu_avg_mw=hw["cpu_gpu_avg"], soc_avg_mw=hw["soc_avg"],
                   energy_per_frame_mj=round(hw["vdd_in_avg"] / fps, 2) if fps > 0 else 0,
                   gpu_mem_peak_mb=0)
        rows.append(row)
        print(f"fps={fps:.1f} pwr={hw['vdd_in_avg']:.0f}mW")

# === STEP 5: Save results ===
out = os.path.join(OUTPUT_DIR, "jetson_tensorrt_profiling.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(f"\nSaved: {out}")

# === STEP 6: Summary ===
print("\n" + "="*60)
print("SUMMARY — Model Variant Comparison")
print("="*60)

for pipe in ["P1_YOLO_Only", "ONLINE_GUARDED", "P3_MOG2"]:
    print(f"\n--- {pipe} ---")
    for variant in ["PyTorch_FP32", "TensorRT_FP32", "TensorRT_FP16", "None"]:
        rs = [r for r in rows if r["pipeline"] == pipe and r["model_variant"] == variant]
        if not rs: continue
        fps_v = [r["fps"] for r in rs if r["fps"] > 0]
        lat_v = [r["avg_latency_ms"] for r in rs if r["avg_latency_ms"] > 0]
        pwr_v = [r["vdd_in_avg_mw"] for r in rs if r["vdd_in_avg_mw"] > 0]
        eng_v = [r["energy_per_frame_mj"] for r in rs if r["energy_per_frame_mj"] > 0]
        act_v = [r["activation_rate"] for r in rs]
        print(f"  {variant}:")
        if fps_v: print(f"    FPS:    {np.mean(fps_v):.1f} avg ({min(fps_v):.1f}-{max(fps_v):.1f})")
        if lat_v: print(f"    Lat:    {np.mean(lat_v):.1f}ms avg")
        if pwr_v: print(f"    Power:  {np.mean(pwr_v):.0f}mW avg")
        if eng_v: print(f"    Energy: {np.mean(eng_v):.1f}mJ/frame")
        if act_v: print(f"    Act:    {np.mean(act_v):.3f}")

# TensorRT speedup
print("\n" + "="*60)
print("TENSORRT SPEEDUP vs PyTorch")
print("="*60)

for pipe in ["P1_YOLO_Only", "ONLINE_GUARDED"]:
    pt_rs = [r for r in rows if r["pipeline"] == pipe and r["model_variant"] == "PyTorch_FP32"]
    fp16_rs = [r for r in rows if r["pipeline"] == pipe and r["model_variant"] == "TensorRT_FP16"]
    fp32_rs = [r for r in rows if r["pipeline"] == pipe and r["model_variant"] == "TensorRT_FP32"]

    if pt_rs:
        pt_fps = np.mean([r["fps"] for r in pt_rs])
        pt_eng = np.mean([r["energy_per_frame_mj"] for r in pt_rs])

        if fp16_rs:
            fp16_fps = np.mean([r["fps"] for r in fp16_rs])
            fp16_eng = np.mean([r["energy_per_frame_mj"] for r in fp16_rs])
            print(f"\n{pipe} TensorRT FP16 vs PyTorch FP32:")
            print(f"  FPS:    {pt_fps:.1f} -> {fp16_fps:.1f} ({fp16_fps/pt_fps:.1f}x speedup)")
            print(f"  Energy: {pt_eng:.1f} -> {fp16_eng:.1f} mJ ({(1-fp16_eng/pt_eng)*100:.0f}% saving)")

        if fp32_rs:
            fp32_fps = np.mean([r["fps"] for r in fp32_rs])
            fp32_eng = np.mean([r["energy_per_frame_mj"] for r in fp32_rs])
            print(f"\n{pipe} TensorRT FP32 vs PyTorch FP32:")
            print(f"  FPS:    {pt_fps:.1f} -> {fp32_fps:.1f} ({fp32_fps/pt_fps:.1f}x speedup)")
            print(f"  Energy: {pt_eng:.1f} -> {fp32_eng:.1f} mJ ({(1-fp32_eng/pt_eng)*100:.0f}% saving)")

print("\nProfiling complete!")
