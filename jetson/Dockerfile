# Canonical pinned Jetson profiling image for the JSA revision (E6).
# Build on-device:  docker build -t l4t-pytorch-asmag:local -f jetson/Dockerfile .
# Pins the stack so absolute edge-GPU numbers are reproducible (the paper's
# original tables used an unpinned pip install; see requirements-jetson.lock
# and software_drift_finding.md).
FROM dustynv/l4t-pytorch:r36.4.0
RUN pip install --index-url https://pypi.org/simple/ ultralytics==8.4.104 psutil \
 && pip install --index-url https://pypi.org/simple/ numpy==1.26.4 --force-reinstall
