#!/bin/bash
echo 'Starting TensorRT profiling in Docker...'
echo 'Image: ghcr.io/lamquocdat01/aap-ai-engine:jetson'
echo 'This may take 30-60 minutes (TensorRT export + profiling)'
docker run --rm --runtime=nvidia --gpus all     -v /home/dat/models:/models     -v /home/dat/cdnet2014:/cdnet2014     -v /home/dat/profiling_results:/output     -v /home/dat/jetson_tensorrt_profiler.py:/profiler.py     ghcr.io/lamquocdat01/aap-ai-engine:jetson     python3 -u /profiler.py     2>&1 | tee /home/dat/profiling_results/tensorrt_profiling.log
echo 'TensorRT profiling complete!'
