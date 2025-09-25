#!/bin/bash
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$APP_DIR/venv/bin/activate"
exec python3 "$APP_DIR/main_application.py"
