# Model weights (not tracked)

The detector weights used by ASMAG-TRC are **not committed** to this repository. They are
large binaries and are covered by the upstream **Ultralytics** license, not this repo's MIT
license — so you must download them locally before running.

## Place in `models/yolo/`

| File | Role | How to obtain |
|---|---|---|
| `yolo26s-seg.pt` | Default detector used throughout the paper | Ultralytics release asset |
| `yolo26s.pt` | Detection-only variant (optional) | Ultralytics release asset |
| `yolov8n.pt` | Detector-generality experiment (E5) | Auto-downloaded by Ultralytics on first use |

With `ultralytics` installed (`pip install -r requirements.txt`), the weights are fetched into
the Ultralytics cache on first `detect()` call; copy the `.pt` into `models/yolo/`, or point
your config's model path at the cached file.

```bash
mkdir -p models/yolo
# then download the weight(s) and place them here, e.g. models/yolo/yolo26s-seg.pt
```

> The weights are subject to Ultralytics' license terms. This repository's MIT license applies
> to the ASMAG-TRC source code only, **not** to the model weights.
