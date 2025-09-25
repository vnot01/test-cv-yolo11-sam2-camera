#!/bin/bash
# Install/enable systemd services for RVM components, including metrics sender
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_DIR="/etc/systemd/system"
PYTHON_BIN="$(command -v python3)"
USER_NAME="${SUDO_USER:-${USER:-my}}"
GROUP_NAME="$USER_NAME"

sudo_run() {
  if [ -n "${RVM_SUDO_PASS:-}" ]; then
    echo "$RVM_SUDO_PASS" | sudo -S "$@"
  else
    sudo "$@"
  fi
}

create_service() {
  local name="$1"
  local exec_start="$2"
  local after_services="$3"
  local file="$SERVICE_DIR/$name.service"
  cat <<EOF | sudo_run tee "$file" >/dev/null
[Unit]
Description=$name
After=network.target network-online.target $after_services
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$GROUP_NAME
WorkingDirectory=$REPO_DIR
ExecStart=$exec_start
Restart=always
RestartSec=3
Environment=PYTHONPATH=$REPO_DIR

[Install]
WantedBy=multi-user.target
EOF
  sudo_run chmod 644 "$file"
}

# Create metrics sender service
METRICS_EXEC="$PYTHON_BIN $REPO_DIR/scripts/run_metrics_sender.py"
create_service "rvm-metrics-sender" "$METRICS_EXEC" ""

# Reload and enable
sudo_run systemctl daemon-reload
sudo_run systemctl enable rvm-metrics-sender.service
sudo_run systemctl restart rvm-metrics-sender.service || true

echo "Metrics sender service installed and started: rvm-metrics-sender.service"



