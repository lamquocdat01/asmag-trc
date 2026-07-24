#!/bin/bash
set -e
echo '=== TensorRT Profiling with Host Power Measurement ==='
echo 'Image: ghcr.io/lamquocdat01/aap-ai-engine:jetson'
echo 'TRT engines already built — skipping export, starting profiling directly'
echo ''

# Write start marker
echo "profiling_start:$(date +%s%3N)" > /home/dat/profiling_results/timing_markers.txt

echo '[1/3] Starting host power logger...'
/home/dat/measure_power.sh /home/dat/profiling_results/trt_power_log.csv 3600 &
POWER_PID=$!
echo "Power logger PID: $POWER_PID"
sleep 2

echo '[2/3] Starting Docker profiling...'
docker run --rm --runtime=nvidia --gpus all     -v /home/dat/models:/models     -v /home/dat/cdnet2014:/cdnet2014     -v /home/dat/profiling_results:/output     -v /home/dat/jetson_tensorrt_profiler.py:/profiler.py     ghcr.io/lamquocdat01/aap-ai-engine:jetson     python3 -u /profiler.py     2>&1 | tee /home/dat/profiling_results/trt_profiling_with_power.log

# Write end marker
echo "profiling_end:$(date +%s%3N)" >> /home/dat/profiling_results/timing_markers.txt

echo '[3/3] Stopping power logger...'
kill $POWER_PID 2>/dev/null
wait $POWER_PID 2>/dev/null

echo ''
echo '=== Power log summary ==='
wc -l /home/dat/profiling_results/trt_power_log.csv
tail -3 /home/dat/profiling_results/trt_power_log.csv
echo 'Done!'
