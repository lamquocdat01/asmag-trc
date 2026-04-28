@echo off
cd /d "%~dp0\.."
python src\run_experiment.py --config configs\debug_one_video.yaml
pause
