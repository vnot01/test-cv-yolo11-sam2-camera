#!/bin/bash

# MyRVM Platform Integration - Deployment Validation Script
# Version: 1.0.0
# Date: September 18, 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/validation.log"

# Default values
ENVIRONMENT="development"
VERBOSE=false
TIMEOUT=300  # 5 minutes timeout

# Functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

show_help() {
    cat << EOF
MyRVM Platform Integration - Deployment Validation Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV    Target environment (development|staging|production)
    -v, --verbose           Enable verbose output
    -t, --timeout SECONDS   Validation timeout in seconds (default: 300)
    -h, --help              Show this help message

Examples:
    $0 -e development       # Validate development deployment
    $0 -e production -v     # Validate production deployment with verbose output

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_error "Valid environments: development, staging, production"
    exit 1
fi

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Start validation
log "🔍 Starting deployment validation for $ENVIRONMENT environment"
log "Timeout: $TIMEOUT seconds"

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Function to run a validation check
run_check() {
    local check_name="$1"
    local check_command="$2"
    local critical="${3:-true}"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    log "Running check: $check_name"
    
    if eval "$check_command" >/dev/null 2>&1; then
        log_success "$check_name - PASSED"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        if [ "$critical" = true ]; then
            log_error "$check_name - FAILED"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        else
            log_warning "$check_name - WARNING"
            WARNING_CHECKS=$((WARNING_CHECKS + 1))
            return 0
        fi
    fi
}

# 1. File System Checks
log "📁 Checking file system..."

run_check "Project root exists" "[ -d '$PROJECT_ROOT' ]"
run_check "Configuration directory exists" "[ -d '$PROJECT_ROOT/config' ]"
run_check "Logs directory exists" "[ -d '$PROJECT_ROOT/logs' ]"
run_check "Scripts directory exists" "[ -d '$PROJECT_ROOT/scripts' ]"

# 2. Configuration Checks
log "⚙️ Checking configuration..."

run_check "Base configuration exists" "[ -f '$PROJECT_ROOT/config/base_config.json' ]"
run_check "Environment configuration exists" "[ -f '$PROJECT_ROOT/config/${ENVIRONMENT}_config.json' ]"
run_check "Configuration is valid JSON" "python3 -m json.tool '$PROJECT_ROOT/config/${ENVIRONMENT}_config.json' >/dev/null"

# 3. Python Environment Checks
log "🐍 Checking Python environment..."

run_check "Python3 is available" "command -v python3"
run_check "Virtual environment exists" "[ -d '$PROJECT_ROOT/venv' ]"
run_check "Requirements file exists" "[ -f '$PROJECT_ROOT/requirements.txt' ]"

# 4. Service Checks
log "🔧 Checking services..."

run_check "Systemd service file exists" "[ -f '/etc/systemd/system/myrvm-integration.service' ]" false
run_check "Service is installed" "systemctl list-unit-files | grep -q myrvm-integration" false

# 5. Network Checks
log "🌐 Checking network connectivity..."

# Get API URL from config
API_URL=$(python3 -c "
import json
try:
    with open('$PROJECT_ROOT/config/${ENVIRONMENT}_config.json', 'r') as f:
        config = json.load(f)
    print(config.get('myrvm_base_url', 'http://localhost:8000'))
except:
    print('http://localhost:8000')
" 2>/dev/null)

run_check "API endpoint is reachable" "curl -s --connect-timeout 10 '$API_URL/health' >/dev/null" false

# 6. Application Checks
log "🚀 Checking application..."

run_check "Main application file exists" "[ -f '$PROJECT_ROOT/main/enhanced_jetson_main.py' ]"
run_check "API client exists" "[ -f '$PROJECT_ROOT/api-client/myrvm_api_client.py' ]"

# 7. Monitoring Checks
log "📊 Checking monitoring..."

run_check "Monitoring dashboard exists" "[ -f '$PROJECT_ROOT/monitoring/dashboard_server.py' ]" false
run_check "Metrics collector exists" "[ -f '$PROJECT_ROOT/monitoring/metrics_collector.py' ]" false

# 8. Backup Checks
log "💾 Checking backup systems..."

run_check "Backup manager exists" "[ -f '$PROJECT_ROOT/backup/backup_manager.py' ]" false
run_check "Recovery manager exists" "[ -f '$PROJECT_ROOT/backup/recovery_manager.py' ]" false

# 9. Performance Checks
log "⚡ Checking performance..."

# Check if system has enough resources
run_check "Sufficient memory available" "[ \$(free -m | awk 'NR==2{printf \"%.0f\", \$7}') -gt 500 ]" false
run_check "Sufficient disk space" "[ \$(df '$PROJECT_ROOT' | awk 'NR==2{print \$4}') -gt 1000000 ]" false

# 10. Security Checks
log "🔒 Checking security..."

run_check "Security manager exists" "[ -f '$PROJECT_ROOT/config/security_manager.py' ]" false
run_check "Logging configuration exists" "[ -f '$PROJECT_ROOT/config/logging_config.py' ]" false

# Wait for service to be ready (if running)
if systemctl is-active --quiet myrvm-integration 2>/dev/null; then
    log "⏳ Waiting for service to be ready..."
    
    for i in $(seq 1 $TIMEOUT); do
        if curl -s --connect-timeout 5 "http://localhost:5002/health" >/dev/null 2>&1; then
            log_success "Service is ready and responding"
            break
        fi
        
        if [ $i -eq $TIMEOUT ]; then
            log_warning "Service did not become ready within timeout"
        else
            sleep 1
        fi
    done
fi

# Final validation summary
log "📊 Validation Summary"
log "===================="
log "Total checks: $TOTAL_CHECKS"
log_success "Passed: $PASSED_CHECKS"
if [ $WARNING_CHECKS -gt 0 ]; then
    log_warning "Warnings: $WARNING_CHECKS"
fi
if [ $FAILED_CHECKS -gt 0 ]; then
    log_error "Failed: $FAILED_CHECKS"
fi

# Determine overall result
if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        log_success "🎉 All validations passed! Deployment is successful."
        exit 0
    else
        log_warning "⚠️  Deployment validation completed with warnings."
        exit 0
    fi
else
    log_error "❌ Deployment validation failed with $FAILED_CHECKS critical errors."
    exit 1
fi
