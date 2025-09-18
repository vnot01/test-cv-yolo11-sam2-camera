#!/bin/bash

# MyRVM Platform Integration - Main Deployment Script
# Version: 1.0.0
# Date: September 18, 2025

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/deployment.log"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOYMENT_DIR="$PROJECT_ROOT"

# Default values
ENVIRONMENT="development"
DRY_RUN=false
VERBOSE=false
SKIP_TESTS=false
FORCE=false

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
MyRVM Platform Integration - Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV    Target environment (development|staging|production)
    -d, --dry-run           Perform a dry run without making changes
    -v, --verbose           Enable verbose output
    -s, --skip-tests        Skip running tests
    -f, --force             Force deployment even if checks fail
    -h, --help              Show this help message

Examples:
    $0 -e development       # Deploy to development
    $0 -e production -d     # Dry run for production
    $0 -e staging -v        # Deploy to staging with verbose output

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
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

# Create necessary directories
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$BACKUP_DIR"

# Start deployment
log "🚀 Starting MyRVM Platform Integration deployment"
log "Environment: $ENVIRONMENT"
log "Project Root: $PROJECT_ROOT"
log "Log File: $LOG_FILE"

if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN MODE - No changes will be made"
fi

# Pre-deployment checks
log "🔍 Running pre-deployment checks..."

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/README.md" ]; then
    log_error "Not in project root directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
log "Python version: $PYTHON_VERSION"

# Check required dependencies
log "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    log_error "Python3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    log_warning "Virtual environment not found, creating one..."
    if [ "$DRY_RUN" = false ]; then
        python3 -m venv "$PROJECT_ROOT/venv"
        source "$PROJECT_ROOT/venv/bin/activate"
        pip install --upgrade pip
    fi
fi

# Activate virtual environment
if [ "$DRY_RUN" = false ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Install/update dependencies
log "📦 Installing dependencies..."
if [ "$DRY_RUN" = false ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
fi

# Run tests (if not skipped)
if [ "$SKIP_TESTS" = false ]; then
    log "🧪 Running tests..."
    if [ "$DRY_RUN" = false ]; then
        cd "$PROJECT_ROOT"
        python -m pytest tests/ -v || {
            if [ "$FORCE" = false ]; then
                log_error "Tests failed. Use --force to deploy anyway."
                exit 1
            else
                log_warning "Tests failed but continuing due to --force flag"
            }
        }
    fi
fi

# Create backup (if not dry run)
if [ "$DRY_RUN" = false ]; then
    log "💾 Creating backup..."
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup configuration files
    cp -r "$PROJECT_ROOT/config" "$BACKUP_PATH/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT/logs" "$BACKUP_PATH/" 2>/dev/null || true
    
    log_success "Backup created: $BACKUP_PATH"
fi

# Deploy based on environment
log "🚀 Deploying to $ENVIRONMENT environment..."

case $ENVIRONMENT in
    development)
        log "Deploying to development environment..."
        if [ "$DRY_RUN" = false ]; then
            # Development deployment
            export MYRVM_ENV=development
            python "$PROJECT_ROOT/main/enhanced_jetson_main.py" --config development
        fi
        ;;
    staging)
        log "Deploying to staging environment..."
        if [ "$DRY_RUN" = false ]; then
            # Staging deployment
            export MYRVM_ENV=staging
            python "$PROJECT_ROOT/main/enhanced_jetson_main.py" --config staging
        fi
        ;;
    production)
        log "Deploying to production environment..."
        if [ "$DRY_RUN" = false ]; then
            # Production deployment
            export MYRVM_ENV=production
            python "$PROJECT_ROOT/main/enhanced_jetson_main.py" --config production
        fi
        ;;
esac

# Post-deployment validation
log "✅ Running post-deployment validation..."

if [ "$DRY_RUN" = false ]; then
    # Check if services are running
    if systemctl is-active --quiet myrvm-integration; then
        log_success "Service is running"
    else
        log_warning "Service is not running"
    fi
    
    # Check configuration
    if [ -f "$PROJECT_ROOT/config/${ENVIRONMENT}_config.json" ]; then
        log_success "Configuration file exists"
    else
        log_error "Configuration file missing"
        exit 1
    fi
fi

# Deployment summary
log_success "🎉 Deployment completed successfully!"
log "Environment: $ENVIRONMENT"
log "Timestamp: $(date)"
log "Log file: $LOG_FILE"

if [ "$DRY_RUN" = true ]; then
    log_warning "This was a dry run - no actual changes were made"
fi

exit 0
