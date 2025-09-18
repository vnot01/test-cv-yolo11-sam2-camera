#!/bin/bash

# MyRVM Platform Integration - Development Deployment Script
# Version: 1.0.0
# Date: September 18, 2025

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying to Development Environment${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run main deployment script with development environment
"$SCRIPT_DIR/deploy.sh" --environment development --verbose

echo -e "${GREEN}✅ Development deployment completed!${NC}"
