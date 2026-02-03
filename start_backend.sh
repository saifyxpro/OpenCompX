#!/bin/bash
# Start the OpenManus Agent S3 Backend
echo "Starting OpenManus Backend..."
pip install -r backend/requirements.txt
bash backend/install_custom_deps.sh
python -m backend.app.main
