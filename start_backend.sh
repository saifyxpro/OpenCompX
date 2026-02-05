#!/bin/bash
# Start the OpenCompX Agent S3 Backend
echo "Starting OpenCompX Backend..."
pip install -r backend/requirements.txt
bash backend/install_custom_deps.sh
python -m backend.app.main
