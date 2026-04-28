@echo off
cd /d "%~dp0\.."
python src\check_cdnet_dataset.py --config configs\q2_core.yaml --output outputs\dataset_audit.csv
pause
