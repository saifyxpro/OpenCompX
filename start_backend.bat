@echo off
echo Starting OpenManus Backend...
pip install -r backend/requirements.txt
python -m backend.app.main
pause
