# Jetson-side profiling & deployment (recovered from device — Phase 0.3)

These scripts were recovered from the Jetson Orin Nano (`dat@dat-desktop`) during the JSA
revision. They previously existed **only on the device** and are the source of the paper's
hardware numbers (Jetson edge-GPU profiling and the **TensorRT FP16 Tables 10–11**). Committed
here so the repository is self-contained.

## Device

- **Jetson Orin Nano 8 GB**, L4T **R36.5.0 (JetPack 6)**, `aarch64`, kernel `5.15.x-tegra`.
- Disk: 227 GB NVMe (~51 GB free at audit).
- **Power:** INA3221 via sysfs hwmon — `/sys/bus/i2c/devices/1-0040/hwmon/hwmon1/` (VDD_IN rail).
  Idle target ≈ **4.86 W** (paper era). Thermal floor ≈ 57 °C; **cooldown gate ≤ 58 °C** between runs.

  **Idle baseline reconciliation (2026-07-24 revision):** measured idle VDD_IN (AAP stopped) =
  **4.47 W** via sysfs (`curr1×in1`, 896 mA × 4.99 V) / **≈4.59 W** via tegrastats — **~0.3–0.4 W
  below** the paper-era 4.86 W. **WiFi `power_save` is NOT the cause** (idle was 4.47 W both on and
  off). The gap is a measurement-floor shift (L4T R36.5 vs the paper era + ambient), not a load
  change. It does **not** affect E6's R3.2 conclusion: the GUARDED_CB-vs-P1-vs-GUARDED energy
  comparison is **relative and all re-measured now under identical conditions**, so the absolute
  floor offset cancels. Reported for transparency.
- Also read via `tegrastats` (VDD_IN, VDD_CPU_GPU_CV, VDD_SOC, GR3D_FREQ, temps).

## Access

- **USB-C device mode (primary, always works):** connect the Jetson's USB-C port to the host.
  A USB-Ethernet gadget appears; the Jetson is at **`192.168.55.1`** (host gets `192.168.55.100`).
  `ssh dat@192.168.55.1`. (ICMP ping is blocked; SSH/TCP works.)
- **Tailscale (when the Jetson has WAN):** `ssh dat@100.72.207.8` (node `dat-desktop`). The tunnel
  only establishes when the device has internet — if it shows `offline`, fall back to USB-C.

## Network / connectivity diagnosis (2026-07-24)

**Symptom:** Tailscale showed `dat-desktop` *offline, last seen ~4 days ago*; the PC could not
SSH it over Tailscale or find it on the Wi-Fi subnet.

**Root cause:** the Jetson was simply **powered off / down for ~4 days** — `uptime` showed
`up 16 minutes` (booted 2026-07-24 19:43). There was **no Wi-Fi driver or profile fault**: on
boot, `wlP1p1s0` (Realtek **RTL8822CE** PCIe adapter) auto-reconnected to SSID **"PhucMinh"**
(`192.168.1.246/24`, signal −45 dBm, full WAN — `ping 8.8.8.8` and DNS both 0 % loss). The saved
NetworkManager profile is intact with `autoconnect=yes`. `nmcli general` → `connected / full`;
`rfkill` → no blocks. Once WAN returned, **Tailscale re-established automatically** (from the PC:
`tailscale ping` → *pong via 192.168.1.246 in 31 ms*; SSH over `100.72.207.8` works).

**Why direct LAN SSH failed even though both are on router "PhucMinh":** the router has
**AP/client isolation** (the Jetson's Wi-Fi AP BSSID `EC:84:B4:BB:AC:6D` is the same router as the
PC gateway `…AC:6C`, yet a full `192.168.1.0/24` port-22 scan from the PC found nothing). Client
isolation blocks PC↔Jetson direct traffic — so **use Tailscale (preferred) or USB-C**, not the LAN IP.

**Stability note for long E6 runs:** Wi-Fi `power_save` is **on** (a known RTL8822CE intermittent-drop
cause). To harden the link before an overnight run:
`sudo iw dev wlP1p1s0 set power_save off` (runtime) or persist via NetworkManager
`nmcli c modify PhucMinh 802-11-wireless.powersave 2`. Regardless, run measurements **detached**
(`nohup`/`tmux`) with an incremental CSV so a transient drop never kills the run.

## On-device layout

| Path | What |
|---|---|
| `~/models/` | `yolo26s.pt`, `yolo26s_fp16.engine`, `yolo26s_fp32.engine`, `yolo26s-seg.*`, `*.onnx` |
| `~/cdnet2014/` | Full CDnet2014 (11 categories, `<cat>/<video>/{input,groundtruth,ROI,temporalROI.txt}`) |
| `~/profiling_results/` | CSV outputs + power logs |
| `~/aap/` | **AAP production stack** (docker-compose; `aicamera_*` containers) — the "37-hour live RTSP deployment" |

## Scripts (in this folder)

| File | Role | Container image |
|---|---|---|
| `jetson_gpu_profiler.py` | Edge GPU profiler: `P1_YOLO_Only`, `P3_MOG2`, `GUARDED`, **`GUARDED_CB`** (new) | `dustynv/l4t-pytorch:r36.4.0` |
| `jetson_tensorrt_profiler.py` | **TensorRT FP16/FP32** profiler → Tables 10–11 (exports engines, profiles P1/P3/GUARDED) | `ghcr.io/lamquocdat01/aap-ai-engine:jetson` |
| `measure_power.sh` | Host-side `tegrastats` power logger (VDD_IN/CPU_GPU/SOC, 0.5 s) → CSV | — |
| `run_gpu_profiling.sh` | Launch wrapper for the edge GPU profiler | — |
| `run_tensorrt_profiling.sh` | Launch wrapper for the TRT profiler | — |
| `run_trt_with_power.sh` | TRT profiling **+ synchronized host power logging** (used for Tables 10–11) | — |
| `circuit_breaker.py` | Co-located copy of `src/safety/circuit_breaker.py` (so `GUARDED_CB` imports inside the container) | — |
| `jetson_gpu_profiler.deployed.py` | Snapshot of the version found on-device (no `GUARDED_CB`) — reference only | — |

## Exact launch commands (with mounts)

**Edge GPU profiling** (`run_gpu_profiling.sh`):
```bash
docker run --rm --runtime=nvidia --gpus all \
  -v /home/dat/models:/models -v /home/dat/cdnet2014:/cdnet2014 \
  -v /home/dat/profiling_results:/output -v /home/dat/jetson_gpu_profiler.py:/profiler.py \
  -v /sys:/sys:ro dustynv/l4t-pytorch:r36.4.0 \
  bash -c "pip install ultralytics psutil numpy==1.26.4 -q && python3 -u /profiler.py"
```

**TensorRT profiling + power** (`run_trt_with_power.sh`): starts `measure_power.sh` on the host,
then:
```bash
docker run --rm --runtime=nvidia --gpus all \
  -v /home/dat/models:/models -v /home/dat/cdnet2014:/cdnet2014 \
  -v /home/dat/profiling_results:/output \
  -v /home/dat/jetson_tensorrt_profiler.py:/profiler.py \
  ghcr.io/lamquocdat01/aap-ai-engine:jetson python3 -u /profiler.py
```

## E6 deployment (running the NEW `GUARDED_CB` pipeline on-device)

The on-device profiler predates the circuit breaker. Before E6:

1. Copy the updated files to the device:
   ```bash
   scp jetson_gpu_profiler.py jetson/circuit_breaker.py dat@192.168.55.1:~/
   scp jetson/circuit_breaker.py dat@192.168.55.1:~/            # co-located for the container
   ```
2. Add a mount so the container can import it, e.g. append to `run_gpu_profiling.sh`:
   `-v /home/dat/circuit_breaker.py:/circuit_breaker.py`
   (the profiler's import is container-robust: it tries `safety.circuit_breaker` then a
   co-located `circuit_breaker`).
3. **Stop the AAP stack first** (frees CPU/GPU and the ~4.86 W idle baseline):
   ```bash
   docker stop $(docker ps -q --filter name=aicamera)
   ```
   Verify idle VDD_IN ≈ 4.86 W and temp ≤ 58 °C before each run; restart AAP afterwards:
   `cd ~/aap && docker compose up -d`.
