#!/bin/bash
# MyRVM Application Deployment Script
# Production deployment automation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Resolve absolute app directory (script/..)
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$APP_DIR/venv"
APP_WRAPPER="$APP_DIR/scripts/run_app_service.sh"
SERVICE_NAME="myrvm-application"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
BACKUP_DIR="/backup/myrvm"
LOG_DIR="$APP_DIR/logs"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

sudo_run() {
  if [ -n "${RVM_SUDO_PASS:-}" ]; then
    echo "$RVM_SUDO_PASS" | sudo -S "$@"
  else
    sudo "$@"
  fi
}

check_requirements() {
  log_info "Checking system requirements..."
  command -v python3 >/dev/null || { log_error "Python3 is not installed"; exit 1; }
  if [ ! -d "$VENV_DIR" ]; then
    log_warning "Virtual environment not found at $VENV_DIR, creating..."
    python3 -m venv "$VENV_DIR"
  fi
  log_success "System requirements check passed"
}

backup_current_deployment() {
  log_info "Creating backup of current deployment..."
  sudo_run mkdir -p "$BACKUP_DIR"
  BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
  sudo_run cp -r "$APP_DIR" "$BACKUP_PATH"
  if [ -f "$SERVICE_FILE" ]; then
    sudo_run cp "$SERVICE_FILE" "$BACKUP_PATH/systemd_service.backup"
  fi
  log_success "Backup created at $BACKUP_PATH"
}

install_dependencies() {
  log_info "Installing Python dependencies..."
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
  pip install --upgrade pip
  if [ -f "$APP_DIR/requirements.txt" ]; then
    pip install -r "$APP_DIR/requirements.txt"
  else
    pip install flask psutil requests websocket-client
  fi
  log_success "Dependencies installed successfully"
}

create_wrapper_script() {
  log_info "Creating application wrapper script..."
  mkdir -p "$APP_DIR/scripts"
  cat > "$APP_WRAPPER" <<'EOF'
#!/bin/bash
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$APP_DIR/venv/bin/activate"
exec python3 "$APP_DIR/main_application.py"
EOF
  chmod +x "$APP_WRAPPER"
  log_success "Wrapper created: $APP_WRAPPER"
}

create_systemd_service() {
  log_info "Creating systemd service file..."
  local tmp_unit="$APP_DIR/.myrvm-application.service.tmp"
  # Discover site-packages path from venv
  local venv_python="$VENV_DIR/bin/python3"
  local site_packages
  site_packages="$($venv_python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' 2>/dev/null || true)"
  if [ -z "$site_packages" ]; then
    # Fallback to common path
    site_packages="$VENV_DIR/lib/python3.10/site-packages"
  fi
  cat > "$tmp_unit" <<EOF
[Unit]
Description=MyRVM Application - Computer Vision Hybrid Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=${SUDO_USER:-${USER}}
Group=${SUDO_USER:-${USER}}
WorkingDirectory=$APP_DIR
Environment=PYTHONPATH=$site_packages
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 $APP_DIR/main_application.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myrvm-application

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=no
ReadWritePaths=$APP_DIR $LOG_DIR $BACKUP_DIR

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
  sudo_run install -m 0644 "$tmp_unit" "$SERVICE_FILE"
  rm -f "$tmp_unit"
  log_success "Systemd service file created"
}

setup_logging() {
  log_info "Setting up logging directories..."
  sudo_run mkdir -p "$LOG_DIR" "$BACKUP_DIR"
  sudo_run chown -R ${SUDO_USER:-${USER}}:${SUDO_USER:-${USER}} "$LOG_DIR" "$BACKUP_DIR"
  log_success "Logging directories created"
}

configure_firewall() {
  log_info "Configuring firewall rules..."
  sudo_run ufw allow 5001/tcp comment "MyRVM GUI Client" 2>/dev/null || log_warning "UFW not available or already configured"
  log_success "Firewall configured"
}

stop_ports() {
  log_info "Stopping RVM services and freeing ports (5000/5001/5002/8080)..."
  sudo_run systemctl stop rvm-remote-camera.service rvm-remote-gui.service rvm-remote-access.service || true
  fuser -k 5000/tcp || true; fuser -k 5001/tcp || true; fuser -k 5002/tcp || true; fuser -k 8080/tcp || true
}

enable_service() {
  log_info "Enabling and starting MyRVM service..."
  sudo_run systemctl daemon-reload
  sudo_run systemctl enable "$SERVICE_NAME"
  sudo_run systemctl restart "$SERVICE_NAME" || true
  sleep 2
  if sudo_run systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "MyRVM service started successfully"
  else
    log_error "Failed to start MyRVM service"
    sudo_run systemctl status "$SERVICE_NAME" --no-pager -l || true
  fi
}

install_rvm_services() {
  log_info "Installing and starting RVM system services (camera/gui/access/metrics)..."
  local installer="$APP_DIR/scripts/install_systemd_services.sh"
  if [ -f "$installer" ]; then
    sudo_run bash "$installer" || true
  else
    log_warning "Installer script not found: $installer"
  fi
  # Ensure core services up (camera/gui/access)
  sudo_run systemctl daemon-reload
  sudo_run systemctl enable rvm-remote-camera.service rvm-remote-gui.service rvm-remote-access.service || true
  sudo_run systemctl restart rvm-remote-camera.service rvm-remote-gui.service rvm-remote-access.service || true
  # Metrics sender (may not exist on first runs)
  sudo_run systemctl enable rvm-metrics-sender.service 2>/dev/null || true
  sudo_run systemctl restart rvm-metrics-sender.service 2>/dev/null || true
}

verify_deployment() {
  log_info "Verifying deployment..."
  sudo_run systemctl is-active --quiet "$SERVICE_NAME" && log_success "Service is running" || log_warning "Service is not active"
  curl -s http://localhost:5001 >/dev/null && log_success "GUI Client is accessible" || log_warning "GUI Client is not accessible"
  log_success "Deployment verification completed"
}

show_status() {
  log_info "MyRVM Application Status:"
  echo "=================================="
  echo "Service Status:"; sudo_run systemctl status "$SERVICE_NAME" --no-pager -l || true
  echo ""; echo "Service Logs (last 10 lines):"; sudo_run journalctl -u "$SERVICE_NAME" -n 10 --no-pager || true
  echo ""; echo "GUI Client: http://localhost:5001"
}

# Main deployment function
deploy() {
  log_info "Starting MyRVM Application deployment..."
  check_requirements
  backup_current_deployment
  install_dependencies
  create_wrapper_script
  create_systemd_service
  setup_logging
  configure_firewall
  stop_ports
  enable_service
  install_rvm_services
  verify_deployment
  log_success "MyRVM Application deployed successfully!"
  show_status
}

# Command line interface
case "${1:-deploy}" in
  "deploy") deploy ;;
  "status") show_status ;;
  "restart") log_info "Restarting MyRVM service..."; sudo_run systemctl restart "$SERVICE_NAME"; log_success "Service restarted"; show_status ;;
  "stop") log_info "Stopping MyRVM service..."; sudo_run systemctl stop "$SERVICE_NAME"; log_success "Service stopped" ;;
  "start") log_info "Starting MyRVM service..."; sudo_run systemctl start "$SERVICE_NAME"; log_success "Service started"; show_status ;;
  "logs") log_info "Showing MyRVM service logs..."; sudo_run journalctl -u "$SERVICE_NAME" -f ;;
  "uninstall") log_warning "Uninstalling MyRVM Application..."; sudo_run systemctl stop "$SERVICE_NAME" 2>/dev/null || true; sudo_run systemctl disable "$SERVICE_NAME" 2>/dev/null || true; sudo_run rm -f "$SERVICE_FILE"; sudo_run systemctl daemon-reload; log_success "MyRVM Application uninstalled" ;;
  *) echo "Usage: $0 {deploy|status|restart|stop|start|logs|uninstall}"; exit 1 ;;
esac
