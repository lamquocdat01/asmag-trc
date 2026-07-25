#!/bin/bash
# Host-side power logger for Jetson Orin Nano
# Logs tegrastats readings while Docker profiling runs
# Usage: ./measure_power.sh <output_csv> <duration_seconds>

OUT=/home/dat/profiling_results/trt_power_log.csv
DUR=3600

echo 'timestamp_ms,vdd_in_mw,cpu_gpu_mw,soc_mw,gpu_pct,ram_mb,temp_cpu_c,temp_gpu_c' > $OUT

END=$((SECONDS + DUR))
while [ $SECONDS -lt $END ]; do
    LINE=$(tegrastats 2>/dev/null | head -1)
    TS=$(date +%s%3N)

    VDD_IN=$(echo "$LINE" | grep -oP 'VDD_IN \K\d+')
    CPU_GPU=$(echo "$LINE" | grep -oP 'VDD_CPU_GPU_CV \K\d+')
    SOC=$(echo "$LINE" | grep -oP 'VDD_SOC \K\d+')
    GPU=$(echo "$LINE" | grep -oP 'GR3D_FREQ \K\d+')
    RAM=$(echo "$LINE" | grep -oP 'RAM \K\d+')
    TEMP_CPU=$(echo "$LINE" | grep -oP 'cpu@\K[\d.]+')
    TEMP_GPU=$(echo "$LINE" | grep -oP 'gpu@\K[\d.]+')

    echo "$TS,${VDD_IN:-0},${CPU_GPU:-0},${SOC:-0},${GPU:-0},${RAM:-0},${TEMP_CPU:-0},${TEMP_GPU:-0}" >> $OUT
    sleep 0.5
done
echo "Power logging done: $OUT"
