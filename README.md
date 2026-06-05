# ASMAG-TRC: Adaptive Safety-Arbitrated Motion-Gated Inference Control for Real-Time Edge AI Surveillance

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![JRTIP](https://img.shields.io/badge/Journal-JRTIP-green.svg)](https://link.springer.com/journal/11554)

Official implementation of the paper:

> **ASMAG-TRC: Adaptive Safety-Arbitrated Motion-Gated Inference Control for Real-Time Edge AI Surveillance Cameras**  
> Dat Lam Quoc  
> *Journal of Real-Time Image Processing (JRTIP), 2026 (under review)*

## Overview

ASMAG-TRC is an adaptive motion-gated inference-control framework that decides **when** to run a deep detector on each video frame rather than running it on every frame. It combines:

- **Lightweight motion proposals** (FrameDiff + MOG2) for activity estimation without YOLO
- **Temporal prediction reuse** to cache and forward recent detections on quiet frames
- **Controller hierarchy**: category-aware → online-calibrated → guarded variants
- **Pure-function safety arbitration** protecting event-critical frames via stateless invariant checks, eliminating the shared-state Heisenbug that plagued earlier observer-based designs

```
Video Frame
    │
    ├── FrameDiff + MOG2 ──→ Motion Features
    │                              │
    │                     Controller Decision
    │                         │         │
    │                    Gate OPEN   Gate CLOSED
    │                         │         │
    │                    Run YOLO   Reuse / Skip
    │                         └────┬────┘
    │                    Safety Arbitration (pure function)
    │                              │
    │                        Final Action
    └────────────────→  DETECT / REUSE / FALLBACK_P3
```

## Results

### CDnet2014 — 53 videos, CPU-only edge profile

| Pipeline | Activation | FPS | Energy/frame (rel.) |
|---|---|---|---|
| P1 (YOLO always-on) | 1.000 | 4.72 | 6.200 |
| P2 (FrameDiff only) | 0.599 | 73.94 | 4.294 |
| P3 (MOG2 only) | 0.809 | 43.78 | 5.744 |
| ASMAG_TR_FAST | 0.664 | 33.03 | 5.145 |
| ASMAG_TR_CONTROLLER | 0.771 | 34.22 | 5.602 |
| ASMAG_TR_CONTROLLER_ONLINE_CALIBRATED | 0.750 | 13.33 | 5.513 |
| **ASMAG_TR_CONTROLLER_ONLINE_GUARDED** | **0.430** | **17.70** | **3.945** |

GUARDED achieves **FMeasure 0.521, Event F1 0.695** — best AE-Score (0.835) combining accuracy and efficiency.

### Jetson Orin Nano — real hardware, GPU + TensorRT FP16

| Pipeline | FPS | Energy/frame |
|---|---|---|
| P1 (YOLO always-on) | 22.83 | 290.8 mJ |
| P3 (MOG2 only) | 272.25 | 30.4 mJ |
| **GUARDED** | **191.74** | **92.6 mJ** |

GUARDED delivers **8.4× speedup** and **68.1% energy reduction** versus always-on YOLO on real hardware (activation = 0.16 on Jetson subset).

### Cross-dataset GUARDED consistency (no retraining)

| Dataset | Videos | Activation | FPS |
|---|---|---|---|
| CDnet2014 (benchmark) | 53 | 0.430 | 17.70 |
| LASIESTA (indoor/outdoor) | 48 | 0.447 | 13.95 |
| VIRAT (real-world surveillance) | 10 | 0.570 | 12.05 |

GUARDED activation never reaches 1.0 on any dataset — it always skips some frames — and the range (0.43–0.57) is consistent across fundamentally different environments.

## Installation

```bash
git clone https://github.com/lamquocdat01/asmag-trc.git
cd asmag-trc
pip install -r requirements.txt
```

Download YOLO26s weights and place in `models/yolo/`:

```bash
mkdir -p models/yolo
# Download yolo26s-seg.pt from ultralytics releases
```

## Usage

### CDnet2014 evaluation

```bash
# Edit dataset path in config first
python src/run_experiment.py --config configs/full_cdnet2014_official_edge_profile_pc.yaml
```

### Cross-dataset evaluation

```bash
python run_cross_dataset.py --config configs/cross_bmc_full.yaml
python run_cross_dataset.py --config configs/cross_lasiesta_full_v2.yaml
python run_cross_dataset.py --config configs/cross_virat_full_v2.yaml
```

### Smoke test (fast, no full dataset needed)

```bash
python run_cross_dataset.py \
    --config configs/cross_virat_full_v2.yaml \
    --videos VIRAT_S_000201_02_000590_000623 \
    --pipelines P3_MOG2 ASMAG_TR_CONTROLLER_ONLINE_GUARDED \
    --max_frames 50
```

### Jetson Orin Nano profiling

```bash
# On Jetson with TensorRT installed
python jetson_gpu_profiler.py
```

## Project Structure

```
asmag-trc/
├── src/
│   ├── run_experiment.py          # Main CDnet2014 runner + all pipeline logic
│   ├── detectors/detectors.py     # YOLO wrapper + MockDetector
│   ├── gating/gates.py            # FrameDiff + MOG2 motion gates
│   ├── metrics/                   # FMeasure, Event F1, mAP50, AE Score, Energy
│   ├── data/cdnet_loader.py       # CDnet2014 loader
│   ├── controller/                # Online mode policy training
│   ├── evaluation/                # Mask-to-box conversion
│   └── utils/                     # I/O helpers, progress monitor
├── run_cross_dataset.py           # Cross-dataset unified evaluator
├── datasets/                      # Adapters: CDnet, BMC, LASIESTA, SBI2015, VIRAT
├── evaluation/                    # Mask normalization, ignore-mask utilities
├── tools/                         # Aggregation, plotting, statistics
├── configs/                       # YAML experiment configurations
├── jetson_gpu_profiler.py         # Jetson Orin Nano hardware profiler
├── models/                        # YOLO weights (not tracked, download separately)
└── outputs/                       # Generated results (gitignored)
```

## Safety Arbitration

The core contribution is `final_safety_arbitration_v2` in `src/run_experiment.py` — a **pure function** that enforces three invariants on a read-only state snapshot, with no side effects:

- **I1 (Normal-frame protection):** Never override actions on quiet frames
- **I2 (Event memory preservation):** Force-refresh when an active event would be missed
- **I3 (Risk-high rescue):** Protect emerging events at high-uncertainty transitions

This pure-function design replaced an earlier observer-based approach that caused a 12-iteration Heisenbug driven by shared mutable state — the refactor is described in the paper.

## Datasets

| Dataset | Videos | Ground Truth | Link |
|---|---|---|---|
| CDnet2014 | 53 | Pixel-level | [jacarini.dinf.usherbrooke.ca](http://jacarini.dinf.usherbrooke.ca/dataset2014) |
| BMC 2012 | 20 | Pixel-level | [backgroundmodelschallenge.eu](https://backgroundmodelschallenge.eu/) |
| LASIESTA | 48 | Pixel-level | [gti.ssr.upm.es](http://www.gti.ssr.upm.es/data/lasiesta) |
| VIRAT | 10 | Event-level | [data.kitware.com](https://data.kitware.com/#collection/56f56db28d777f753209ba9f) |

Place each dataset in `datasets/<name>/` and point the corresponding config at it.

## Citation

```bibtex
@article{lam2026asmag,
  title   = {ASMAG-TRC: Adaptive Safety-Arbitrated Motion-Gated Inference Control
             for Real-Time Edge AI Surveillance Cameras},
  author  = {Lam Quoc, Dat},
  journal = {Journal of Real-Time Image Processing},
  year    = {2026},
  publisher = {Springer}
}
```

## License

MIT — see [LICENSE](LICENSE).

## Contact

Dat Lam Quoc · lamquocdat@gmail.com · FPT University, Ho Chi Minh City, Vietnam
