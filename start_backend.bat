@echo off
echo Starting OpenCompX Backend...
pip install -r backend/requirements.txt
python -m backend.app.main
pause
