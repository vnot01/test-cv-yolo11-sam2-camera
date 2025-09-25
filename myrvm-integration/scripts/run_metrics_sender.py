#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from monitoring.metrics_sender import MetricsSender  # noqa: E402


def load_config():
    # Try production_config.json
    cfg_path = PROJECT_ROOT / 'config' / 'production_config.json'
    if cfg_path.exists():
        try:
            with open(cfg_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def main():
    cfg = load_config()

    # Resolve server_url, rvm_id, api_key
    server_url = os.environ.get('MYRVM_SERVER_URL') \
        or cfg.get('server_url') \
        or cfg.get('remote_access', {}).get('server_url') \
        or 'http://localhost:8001'

    rvm_id = os.environ.get('RVM_ID') \
        or cfg.get('rvm_id') \
        or cfg.get('remote_access', {}).get('rvm_id') \
        or 1
    try:
        rvm_id = int(rvm_id)
    except Exception:
        rvm_id = 1

    api_key = os.environ.get('MYRVM_API_KEY') \
        or cfg.get('remote_access', {}).get('api_key') \
        or os.environ.get('API_KEY') \
        or ''

    interval = int(os.environ.get('METRICS_INTERVAL') 
                   or cfg.get('remote_access', {}).get('metrics_interval') 
                   or cfg.get('monitoring_interval') 
                   or '300')  # default 5 min

    sender = MetricsSender(server_url, rvm_id, api_key)
    sender.send_interval = interval
    sender.start()

    # Run indefinitely
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        sender.stop()


if __name__ == '__main__':
    main()
