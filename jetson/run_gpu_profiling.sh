#!/bin/bash
mkdir -p /home/dat/profiling_results
echo Starting GPU profiling with power measurement...
docker run --rm --runtime=nvidia --gpus all \
    -v /home/dat/models:/models \
    -v /home/dat/cdnet2014:/cdnet2014 \
    -v /home/dat/profiling_results:/output \
    -v /home/dat/jetson_gpu_profiler.py:/profiler.py \
    -v /sys:/sys:ro \
    dustynv/l4t-pytorch:r36.4.0 \
    bash -c "pip install --index-url https://pypi.org/simple/ ultralytics psutil 2>&1|tail -2 && pip install --index-url https://pypi.org/simple/ numpy==1.26.4 --force-reinstall -q && echo setup_ok && python3 -u /profiler.py"

echo Done: $?
