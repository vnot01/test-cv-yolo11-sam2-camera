#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$REPO_ROOT/venv/bin/python3"

# Service names
CAMERA_UNIT="rvm-remote-camera.service"
GUI_UNIT="rvm-remote-gui.service"
ACCESS_UNIT="rvm-remote-access.service"

SYSTEMD_DIR="/etc/systemd/system"

create_unit_files() {
  sudo tee "$SYSTEMD_DIR/$CAMERA_UNIT" >/dev/null <<UNIT
[Unit]
Description=RVM Remote Camera Service (port 5000)
After=network.target

[Service]
Type=simple
WorkingDirectory=$REPO_ROOT
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_BIN services/remote_camera_service.py
Restart=on-failure
RestartSec=3
User=my

[Install]
WantedBy=multi-user.target
UNIT

  sudo tee "$SYSTEMD_DIR/$GUI_UNIT" >/dev/null <<UNIT
[Unit]
Description=RVM Remote GUI Service (port 5001)
After=network.target

[Service]
Type=simple
WorkingDirectory=$REPO_ROOT
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_BIN services/remote_gui_service.py
Restart=on-failure
RestartSec=3
User=my

[Install]
WantedBy=multi-user.target
UNIT

  sudo tee "$SYSTEMD_DIR/$ACCESS_UNIT" >/dev/null <<UNIT
[Unit]
Description=RVM Remote Access Controller (port 5002)
After=network.target

[Service]
Type=simple
WorkingDirectory=$REPO_ROOT
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_BIN services/remote_access_controller.py --port 5002
Restart=on-failure
RestartSec=3
User=my

[Install]
WantedBy=multi-user.target
UNIT
}

enable_and_start() {
  sudo systemctl daemon-reload
  sudo systemctl enable "$CAMERA_UNIT" "$GUI_UNIT" "$ACCESS_UNIT"
  sudo systemctl restart "$CAMERA_UNIT" "$GUI_UNIT" "$ACCESS_UNIT"
}

main() {
  create_unit_files
  enable_and_start
  echo "Systemd services installed and started: $CAMERA_UNIT, $GUI_UNIT, $ACCESS_UNIT"
}

main "$@"



