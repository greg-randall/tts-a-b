#!/bin/sh
# Copy this to run.sh and fill in the values for your environment.
cd /path/to/your/app
export SECRET_KEY=$(grep SECRET_KEY /path/to/secrets.env | cut -d= -f2)
# Adjust workers (-w), bind address/port (-b), and SCRIPT_NAME as needed.
# If running at the root (not a subpath), remove --env SCRIPT_NAME entirely.
exec /path/to/venv/bin/gunicorn -w 2 -b 127.0.0.1:8001 --env SCRIPT_NAME=/your-subpath app:app
