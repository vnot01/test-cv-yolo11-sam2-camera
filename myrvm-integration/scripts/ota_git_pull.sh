#!/bin/bash
# OTA Git Pull Script for MyRVM Integration
# - Stops RVM services
# - git fetch/pull latest changes
# - Downloads required models
# - Writes version metadata files
# - Restarts RVM services
# - Logs to logs/ota_pull.log

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_DIR/logs"
MODELS_DIR="$REPO_DIR/models"
LOG_FILE="$LOG_DIR/ota_pull.log"
STATUS_FILE="$LOG_DIR/ota_pull.status"

# Model URLs (can be overridden via env)
RVM_MODEL_URL="${RVM_MODEL_URL:-https://github.com/vnot01/MySuperApps/releases/download/v1.0.0/best.pt}"
SAM2_MODEL_URL="${SAM2_MODEL_URL:-https://github.com/ultralytics/assets/releases/download/v8.3.0/sam2.1_b.pt}"
YOLO11_MODEL_URL="${YOLO11_MODEL_URL:-https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt}"

# Service names
SERVICES=("rvm-remote-camera.service" "rvm-remote-gui.service" "rvm-remote-access.service")

mkdir -p "$LOG_DIR" "$MODELS_DIR"

echo "$(date -Iseconds) START OTA_PULL" | tee -a "$LOG_FILE"
echo "running" > "$STATUS_FILE"

run() {
  echo "$(date -Iseconds) $*" | tee -a "$LOG_FILE"
  "$@" 2>&1 | tee -a "$LOG_FILE"
}

sudo_run() {
  if [ -n "${RVM_SUDO_PASS:-}" ]; then
    echo "$RVM_SUDO_PASS" | sudo -S "$@"
  else
    sudo "$@"
  fi
}

stop_services() {
  for svc in "${SERVICES[@]}"; do
    sudo_run systemctl stop "$svc" || true
  done
}

start_services() {
  sudo_run systemctl daemon-reload || true
  for svc in "${SERVICES[@]}"; do
    sudo_run systemctl restart "$svc" || true
  done
}

pull_repo() {
  cd "$REPO_DIR"
  run git fetch --all --prune
  # Prefer hard reset to main for deterministic deployments, fallback to pull
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    run git reset --hard origin/main
  else
    run git pull --rebase || true
  fi
}

parse_version_from_url() {
  # Extract version tag between /download/ and next /
  local url="$1"
  local tag
  tag=$(echo "$url" | sed -n 's#.*/download/\([^/]*\)/.*#\1#p')
  if [ -z "$tag" ]; then
    tag="unknown"
  fi
  echo "$tag"
}

download_models() {
  local rvm_ver sam2_ver yolo_ver
  rvm_ver=$(parse_version_from_url "$RVM_MODEL_URL")
  sam2_ver=$(parse_version_from_url "$SAM2_MODEL_URL")
  yolo_ver=$(parse_version_from_url "$YOLO11_MODEL_URL")

  run bash -lc "curl -L --retry 3 --retry-delay 2 -o '$MODELS_DIR/best.pt' '$RVM_MODEL_URL'"
  echo "$rvm_ver" > "$MODELS_DIR/best.pt.version"

  run bash -lc "curl -L --retry 3 --retry-delay 2 -o '$MODELS_DIR/sam2.1_b.pt' '$SAM2_MODEL_URL'"
  echo "$sam2_ver" > "$MODELS_DIR/sam2.1_b.pt.version"

  run bash -lc "curl -L --retry 3 --retry-delay 2 -o '$MODELS_DIR/yolo11m.pt' '$YOLO11_MODEL_URL'"
  echo "$yolo_ver" > "$MODELS_DIR/yolo11m.pt.version"
}

main() {
  stop_services
  pull_repo
  download_models
  start_services
  echo "$(date -Iseconds) DONE" | tee -a "$LOG_FILE"
  echo "done" > "$STATUS_FILE"
}

trap 'echo "$(date -Iseconds) ERROR" | tee -a "$LOG_FILE"; echo "error" > "$STATUS_FILE"' ERR

main "$@"
