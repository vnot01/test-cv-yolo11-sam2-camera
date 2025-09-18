#!/bin/bash

# MyRVM Platform Integration - Staging Deployment Script
# Version: 1.0.0
# Date: September 18, 2025

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying to Staging Environment${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Confirm staging deployment
echo -e "${YELLOW}⚠️  This will deploy to the staging environment. Continue? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Run main deployment script with staging environment
"$SCRIPT_DIR/deploy.sh" --environment staging --verbose

echo -e "${GREEN}✅ Staging deployment completed!${NC}"
