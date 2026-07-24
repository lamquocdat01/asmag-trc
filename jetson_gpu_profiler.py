import os, sys, time, csv, threading, subprocess, re, warnings, psutil
import numpy as np
import cv2
warnings.filterwarnings("ignore")
import torch
from ultralytics import YOLO

# E1 [R3.2] Persistent-motion circuit breaker — shared with the CPU runner
# (src/safety/circuit_breaker.py). The repo's src/ must be present on device;
# see jetson/README.md.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from safety.circuit_breaker import PersistentMotionCircuitBreaker

CB_CFG = {"enabled": True, "theta_high": 0.85, "theta_low": 0.60,
          "window": 60, "probe_every": 300, "probe_len": 30}

print(f"torch {torch.__version__} CUDA:{torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB")

model = YOLO("/models/yolo26s.pt")
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Inference device: {device}")
print(f"Model size: {os.path.getsize('/models/yolo26s.pt')/1024/1024:.1f} MB")

dummy = np.zeros((480, 640, 3), dtype=np.uint8)
for _ in range(20):
    model(dummy, verbose=False, device=device)
if torch.cuda.is_available():
    torch.cuda.synchronize()
print("GPU warmup done")


class TegrastatsLogger:
    def __init__(self):
        self.power_vdd_in = []
        self.power_cpu_gpu_cv = []
        self.power_soc = []
        self.gpu_pct = []
        self.cpu_pct = []
        self.ram_mb = []
        self.temp_c = []
        self._running = False

    def start(self):
        self.power_vdd_in = []
        self.power_cpu_gpu_cv = []
        self.power_soc = []
        self.gpu_pct = []
        self.cpu_pct = []
        self.ram_mb = []
        self.temp_c = []
        self._running = True
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        time.sleep(0.7)

    def stop(self):
        self._running = False
        if hasattr(self, "_p"):
            try:
                self._p.terminate()
            except Exception:
                pass
        self._t.join(timeout=3)

    def _run(self):
        # Try tegrastats first; fall back to INA3221 sysfs (works inside Docker with -v /sys:/sys)
        if os.path.exists("/usr/bin/tegrastats"):
            try:
                self._p = subprocess.Popen(
                    ["/usr/bin/tegrastats", "--interval", "500"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                while self._running:
                    line = self._p.stdout.readline()
                    if not line:
                        break
                    self._parse(line)
                return
            except Exception:
                pass
        # Sysfs fallback: INA3221 on /sys/class/hwmon/hwmon1
        HWM = "/sys/class/hwmon/hwmon1"
        while self._running:
            try:
                v1 = int(open(f"{HWM}/in1_input").read().strip())
                i1 = int(open(f"{HWM}/curr1_input").read().strip())
                self.power_vdd_in.append(v1 * i1 // 1000)
                try:
                    v2 = int(open(f"{HWM}/in2_input").read().strip())
                    i2 = int(open(f"{HWM}/curr2_input").read().strip())
                    self.power_cpu_gpu_cv.append(v2 * i2 // 1000)
                except Exception:
                    pass
                try:
                    v3 = int(open(f"{HWM}/in3_input").read().strip())
                    i3 = int(open(f"{HWM}/curr3_input").read().strip())
                    self.power_soc.append(v3 * i3 // 1000)
                except Exception:
                    pass
            except Exception:
                pass
            time.sleep(0.5)

    def _parse(self, line):
        m = re.search(r"VDD_IN\s+(\d+)", line)
        if m:
            self.power_vdd_in.append(int(m.group(1)))
        m = re.search(r"VDD_CPU_GPU_CV\s+(\d+)", line)
        if m:
            self.power_cpu_gpu_cv.append(int(m.group(1)))
        m = re.search(r"VDD_SOC\s+(\d+)", line)
        if m:
            self.power_soc.append(int(m.group(1)))
        m = re.search(r"GR3D_FREQ\s+(\d+)%", line)
        if m:
            self.gpu_pct.append(int(m.group(1)))
        cpus = re.findall(r"(\d+)%@", line)
        if cpus:
            self.cpu_pct.append(np.mean([int(c) for c in cpus]))
        m = re.search(r"RAM\s+(\d+)/(\d+)MB", line)
        if m:
            self.ram_mb.append(int(m.group(1)))
        temps = re.findall(r"@(\d+\.?\d*)C", line)
        if temps:
            self.temp_c.append(max(float(t) for t in temps))

    def summary(self):
        def safe_mean(lst):
            return float(np.mean(lst)) if lst else 0.0
        def safe_p90(lst):
            return float(np.percentile(lst, 90)) if lst else 0.0
        def safe_max(lst):
            return float(max(lst)) if lst else 0.0
        return {
            "vdd_in_avg_mw": round(safe_mean(self.power_vdd_in), 1),
            "vdd_in_p90_mw": round(safe_p90(self.power_vdd_in), 1),
            "vdd_cpu_gpu_avg_mw": round(safe_mean(self.power_cpu_gpu_cv), 1),
            "vdd_soc_avg_mw": round(safe_mean(self.power_soc), 1),
            "gpu_avg_pct": round(safe_mean(self.gpu_pct), 1),
            "gpu_max_pct": round(safe_max(self.gpu_pct), 1),
            "cpu_avg_pct": round(safe_mean(self.cpu_pct), 1),
            "ram_avg_mb": round(safe_mean(self.ram_mb), 0),
            "ram_max_mb": round(safe_max(self.ram_mb), 0),
            "temp_avg_c": round(safe_mean(self.temp_c), 1),
            "temp_max_c": round(safe_max(self.temp_c), 1),
            "n_samples": len(self.power_vdd_in),
        }


VIDEOS_ROOT = "/cdnet2014"
videos = []
for cat in sorted(os.listdir(VIDEOS_ROOT)):
    cd = os.path.join(VIDEOS_ROOT, cat)
    if not os.path.isdir(cd):
        continue
    for vid in sorted(os.listdir(cd)):
        vd = os.path.join(cd, vid)
        inp = os.path.join(vd, "input")
        if os.path.isdir(inp):
            videos.append((cat, vid, inp))

print(f"Videos: {len(videos)}")
WARMUP = 10
rows = []

first_frame = cv2.imread(os.path.join(videos[0][2], sorted(os.listdir(videos[0][2]))[0]))
H, W = first_frame.shape[:2] if first_frame is not None else (0, 0)
print(f"Input resolution: {W}x{H}")

if torch.cuda.is_available():
    gpu_mem_before = torch.cuda.memory_allocated() / 1024**2
    print(f"GPU memory allocated (after warmup): {gpu_mem_before:.1f} MB")

FIELDS = [
    "category", "video", "pipeline", "n_frames", "resolution",
    "fps", "throughput_total_s",
    "avg_latency_ms", "p90_latency_ms", "max_latency_ms",
    "activation_rate",
    "vdd_in_avg_mw", "vdd_in_p90_mw",
    "vdd_cpu_gpu_avg_mw", "vdd_soc_avg_mw",
    "energy_per_frame_mj",
    "gpu_avg_pct", "gpu_max_pct",
    "cpu_avg_pct",
    "ram_avg_mb", "ram_max_mb",
    "gpu_mem_peak_mb",
    "temp_avg_c", "temp_max_c",
    "cb_entered", "cb_bypass_frames", "cb_bypass_rate",
]

for cat, vid, idir in videos:
    files = sorted(f for f in os.listdir(idir) if f.endswith((".jpg", ".png")))
    print(f"\n--- {cat}/{vid} ({len(files)} frames, {W}x{H}) ---")

    for pipe in ["P1_YOLO_Only", "P3_MOG2", "GUARDED", "GUARDED_CB"]:
        print(f"  {pipe} ... ", end="", flush=True)
        bg = cv2.createBackgroundSubtractorMOG2(200, 16, True) if pipe != "P1_YOLO_Only" else None
        lat, yolo_n = [], 0
        cb = PersistentMotionCircuitBreaker(CB_CFG) if pipe == "GUARDED_CB" else None
        cb_prev_motion = 1.0
        cb_bypass_n = 0
        tg = TegrastatsLogger()

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        tg.start()
        t_total_start = time.perf_counter()

        for i, fn in enumerate(files):
            frame = cv2.imread(os.path.join(idir, fn))
            if frame is None:
                continue

            if torch.cuda.is_available():
                torch.cuda.synchronize()
            t0 = time.perf_counter()

            if pipe == "P1_YOLO_Only":
                with torch.no_grad():
                    model(frame, verbose=False, device=device)
                if i >= WARMUP:
                    yolo_n += 1
            elif pipe == "P3_MOG2":
                bg.apply(frame)
            elif pipe == "GUARDED":
                mask = bg.apply(frame)
                ratio = np.count_nonzero(mask > 127) / mask.size
                if ratio > 0.02:
                    with torch.no_grad():
                        model(frame, verbose=False, device=device)
                    if i >= WARMUP:
                        yolo_n += 1
            else:  # GUARDED_CB — circuit breaker skips MOG2 during persistent motion
                dec = cb.step(cb_prev_motion)
                if dec["cb_bypass_active"]:
                    # BYPASS: skip bg.apply() entirely, detect every frame (P1 behaviour)
                    with torch.no_grad():
                        model(frame, verbose=False, device=device)
                    if i >= WARMUP:
                        yolo_n += 1
                        cb_bypass_n += 1
                else:
                    # ACTIVE/PROBE: run MOG2, measure motion, feed the breaker
                    mask = bg.apply(frame)
                    ratio = np.count_nonzero(mask > 127) / mask.size
                    cb_prev_motion = 1.0 if ratio > 0.02 else 0.0
                    if ratio > 0.02:
                        with torch.no_grad():
                            model(frame, verbose=False, device=device)
                        if i >= WARMUP:
                            yolo_n += 1

            if torch.cuda.is_available():
                torch.cuda.synchronize()

            if i >= WARMUP:
                lat.append((time.perf_counter() - t0) * 1000)

        t_total = time.perf_counter() - t_total_start
        tg.stop()

        if not lat:
            print("SKIP")
            continue

        n = len(lat)
        act = 1.0 if pipe == "P1_YOLO_Only" else (0.0 if pipe == "P3_MOG2" else yolo_n / n)
        fps = 1000.0 / np.mean(lat)
        hw = tg.summary()
        energy_mj = hw["vdd_in_avg_mw"] / fps if fps > 0 else 0
        gpu_mem_peak = torch.cuda.max_memory_allocated() / 1024**2 if torch.cuda.is_available() else 0

        row = {
            "category": cat, "video": vid, "pipeline": pipe,
            "n_frames": n, "resolution": f"{W}x{H}",
            "fps": round(fps, 2),
            "throughput_total_s": round(t_total, 2),
            "avg_latency_ms": round(float(np.mean(lat)), 2),
            "p90_latency_ms": round(float(np.percentile(lat, 90)), 2),
            "max_latency_ms": round(float(np.max(lat)), 2),
            "activation_rate": round(act, 4),
            "vdd_in_avg_mw": hw["vdd_in_avg_mw"],
            "vdd_in_p90_mw": hw["vdd_in_p90_mw"],
            "vdd_cpu_gpu_avg_mw": hw["vdd_cpu_gpu_avg_mw"],
            "vdd_soc_avg_mw": hw["vdd_soc_avg_mw"],
            "energy_per_frame_mj": round(energy_mj, 2),
            "gpu_avg_pct": hw["gpu_avg_pct"],
            "gpu_max_pct": hw["gpu_max_pct"],
            "cpu_avg_pct": hw["cpu_avg_pct"],
            "ram_avg_mb": hw["ram_avg_mb"],
            "ram_max_mb": hw["ram_max_mb"],
            "gpu_mem_peak_mb": round(gpu_mem_peak, 1),
            "temp_avg_c": hw["temp_avg_c"],
            "temp_max_c": hw["temp_max_c"],
            "cb_entered": (cb.cb_entered if cb else 0),
            "cb_bypass_frames": cb_bypass_n,
            "cb_bypass_rate": round(cb_bypass_n / n, 4) if n else 0.0,
        }
        rows.append(row)
        print(f"fps={fps:.1f} act={act:.2f} pwr={hw['vdd_in_avg_mw']:.0f}mW gpu={hw['gpu_avg_pct']:.0f}% temp={hw['temp_max_c']:.0f}C")

out = "/output/jetson_gpu_profiling.csv"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(f"\nSaved: {out}")

print("\n===== SYSTEM INFO =====")
print(f"Platform: Jetson Orin Nano")
print(f"torch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory Total: {torch.cuda.get_device_properties(0).total_memory/1024**2:.0f} MB")
print(f"Model: yolo26s.pt ({os.path.getsize('/models/yolo26s.pt')/1024/1024:.1f} MB)")
print(f"Resolution: {W}x{H}")

print("\n===== PIPELINE SUMMARY =====")
for p in ["P1_YOLO_Only", "P3_MOG2", "GUARDED", "GUARDED_CB"]:
    rs = [r for r in rows if r["pipeline"] == p]
    if not rs:
        continue
    print(f"\n{p}:")
    print(f"  FPS:        {np.mean([r['fps'] for r in rs]):.1f} avg")
    print(f"  Latency:    {np.mean([r['avg_latency_ms'] for r in rs]):.1f}ms avg, P90={np.mean([r['p90_latency_ms'] for r in rs]):.1f}ms")
    print(f"  Activation: {np.mean([r['activation_rate'] for r in rs]):.3f}")
    print(f"  VDD_IN:     {np.mean([r['vdd_in_avg_mw'] for r in rs]):.0f}mW avg")
    print(f"  CPU_GPU_CV: {np.mean([r['vdd_cpu_gpu_avg_mw'] for r in rs]):.0f}mW avg")
    print(f"  Energy:     {np.mean([r['energy_per_frame_mj'] for r in rs]):.1f}mJ/frame")
    print(f"  GPU%:       {np.mean([r['gpu_avg_pct'] for r in rs]):.0f}% avg, max={max(r['gpu_max_pct'] for r in rs):.0f}%")
    print(f"  CPU%:       {np.mean([r['cpu_avg_pct'] for r in rs]):.0f}% avg")
    print(f"  RAM:        {np.mean([r['ram_avg_mb'] for r in rs]):.0f}MB avg, max={max(r['ram_max_mb'] for r in rs):.0f}MB")
    print(f"  Temp:       {np.mean([r['temp_avg_c'] for r in rs]):.1f}C avg, max={max(r['temp_max_c'] for r in rs):.1f}C")

p1_rs = [r for r in rows if r["pipeline"] == "P1_YOLO_Only"]
gu_rs = [r for r in rows if r["pipeline"] == "GUARDED"]
if p1_rs and gu_rs:
    print("\n===== GUARDED vs P1_YOLO_Only =====")
    p1_fps = np.mean([r["fps"] for r in p1_rs])
    gu_fps = np.mean([r["fps"] for r in gu_rs])
    p1_pwr = np.mean([r["vdd_in_avg_mw"] for r in p1_rs])
    gu_pwr = np.mean([r["vdd_in_avg_mw"] for r in gu_rs])
    p1_eng = np.mean([r["energy_per_frame_mj"] for r in p1_rs])
    gu_eng = np.mean([r["energy_per_frame_mj"] for r in gu_rs])
    print(f"  FPS:    {p1_fps:.1f} -> {gu_fps:.1f} ({gu_fps/p1_fps:.1f}x speedup)")
    print(f"  Power:  {p1_pwr:.0f} -> {gu_pwr:.0f}mW ({(1-gu_pwr/p1_pwr)*100:.0f}% saving)")
    print(f"  Energy: {p1_eng:.1f} -> {gu_eng:.1f}mJ ({(1-gu_eng/p1_eng)*100:.0f}% saving)")
    print(f"  Act:    1.000 -> {np.mean([r['activation_rate'] for r in gu_rs]):.3f}")

cb_rs = [r for r in rows if r["pipeline"] == "GUARDED_CB"]
if p1_rs and cb_rs:
    print("\n===== GUARDED_CB vs P1_YOLO_Only (circuit breaker) =====")
    p1_eng = np.mean([r["energy_per_frame_mj"] for r in p1_rs])
    cb_eng = np.mean([r["energy_per_frame_mj"] for r in cb_rs])
    cb_pwr = np.mean([r["vdd_in_avg_mw"] for r in cb_rs])
    p1_pwr = np.mean([r["vdd_in_avg_mw"] for r in p1_rs])
    print(f"  Power:  {p1_pwr:.0f} -> {cb_pwr:.0f}mW")
    print(f"  Energy: {p1_eng:.1f} -> {cb_eng:.1f}mJ/frame  (target: <= P1 + epsilon)")
    print(f"  Bypass: {np.mean([r['cb_bypass_rate'] for r in cb_rs])*100:.1f}% of frames, "
          f"entered on {sum(1 for r in cb_rs if r['cb_entered'] > 0)}/{len(cb_rs)} videos")
    if gu_rs:
        gu_eng = np.mean([r["energy_per_frame_mj"] for r in gu_rs])
        print(f"  vs GUARDED: {gu_eng:.1f} -> {cb_eng:.1f}mJ/frame "
              f"({(1-cb_eng/gu_eng)*100:+.1f}% vs guarded)")
