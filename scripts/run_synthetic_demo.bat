@echo off
cd /d "%~dp0\.."
python src\run_experiment.py --config configs\synthetic_demo.yaml
pause
