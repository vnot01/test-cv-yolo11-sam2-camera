#!/bin/bash

# MyRVM Platform Integration - Production Deployment Script
# Version: 1.0.0
# Date: September 18, 2025

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying to Production Environment${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Production deployment confirmation
echo -e "${RED}⚠️  WARNING: This will deploy to the PRODUCTION environment!${NC}"
echo -e "${YELLOW}This action will affect live users and systems.${NC}"
echo ""
echo -e "${YELLOW}Are you sure you want to continue? (type 'yes' to confirm)${NC}"
read -r response
if [[ "$response" != "yes" ]]; then
    echo "Production deployment cancelled."
    exit 0
fi

# Additional confirmation
echo -e "${YELLOW}Please type 'DEPLOY TO PRODUCTION' to confirm:${NC}"
read -r final_confirmation
if [[ "$final_confirmation" != "DEPLOY TO PRODUCTION" ]]; then
    echo "Production deployment cancelled."
    exit 0
fi

# Run main deployment script with production environment
"$SCRIPT_DIR/deploy.sh" --environment production --verbose

echo -e "${GREEN}✅ Production deployment completed!${NC}"
echo -e "${YELLOW}📊 Please monitor the system for any issues.${NC}"
