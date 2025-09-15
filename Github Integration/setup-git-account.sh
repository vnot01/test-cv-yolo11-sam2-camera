#!/bin/bash
# GitHub Multi-Account Setup Script
# Usage: ./setup-git-account.sh <repo-name> <github-user> <token>

REPO_NAME=$1
GITHUB_USER=$2
TOKEN=$3

if [ -z "$REPO_NAME" ] || [ -z "$GITHUB_USER" ] || [ -z "$TOKEN" ]; then
    echo "Usage: $0 <repo-name> <github-user> <token>"
    echo "Example: $0 test-cv-yolo11-sam2-camera vnot01 github_pat_..."
    exit 1
fi

# Set git config
git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_USER@example.com"

# Set remote
git remote set-url origin https://$GITHUB_USER:$TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git

echo "Git setup completed for $GITHUB_USER/$REPO_NAME"
echo "Repository URL: https://github.com/$GITHUB_USER/$REPO_NAME"
