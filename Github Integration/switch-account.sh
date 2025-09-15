#!/bin/bash
# GitHub Account Switch Script
# Usage: ./switch-account.sh <account-name>

ACCOUNT=$1

case $ACCOUNT in
    "vnot01")
        git config --global user.name "vnot01"
        git config --global user.email "vnot01@example.com"
        echo "Switched to vnot01 account"
        ;;
    "myotheruser")
        git config --global user.name "myotheruser"
        git config --global user.email "myotheruser@example.com"
        echo "Switched to myotheruser account"
        ;;
    *)
        echo "Usage: $0 [vnot01|myotheruser]"
        echo "Available accounts:"
        echo "  vnot01      - Primary account"
        echo "  myotheruser - Secondary account"
        ;;
esac
