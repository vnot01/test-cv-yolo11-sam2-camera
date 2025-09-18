#!/usr/bin/env python3
"""
Health Check Endpoint for MyRVM Platform Integration
"""

import sys
import json
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "main"))

def health_check():
    """Perform health check"""
    try:
        # Import main service
        from enhanced_jetson_main import EnhancedJetsonMain
        
        # Check if service is running
        # This is a simplified check - in production, you'd want more comprehensive checks
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'myrvm-integration'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'service': 'myrvm-integration'
        }

if __name__ == "__main__":
    result = health_check()
    print(json.dumps(result))
    sys.exit(0 if result['status'] == 'healthy' else 1)
