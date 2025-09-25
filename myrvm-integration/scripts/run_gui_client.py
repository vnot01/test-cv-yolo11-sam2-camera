#!/usr/bin/env python3
"""
Script to run GUI Client for user interaction
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from gui.gui_client import GUIClient

def main():
    """Main function to start GUI Client"""
    try:
        # Load configuration
        config_path = project_root / 'config' / 'production_config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get RVM ID
        rvm_id = str(config.get('remote_access', {}).get('rvm_id', 1))
        
        # Create and start GUI Client
        client = GUIClient(rvm_id, '0.0.0.0', 5001)
        print(f"Starting GUI Client for RVM {rvm_id} on port 5001...")
        client.start()
        
    except Exception as e:
        print(f"Error starting GUI Client: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
