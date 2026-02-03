#!/bin/bash
# Start the OpenManus Agent S3 Backend
echo "Starting OpenManus Backend..."
pip install -r backend/requirements.txt
python -m backend.app.main
