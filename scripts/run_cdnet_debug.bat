@echo off
cd /d "%~dp0\.."
python src\run_experiment.py --config configs\q2_core.yaml
pause
