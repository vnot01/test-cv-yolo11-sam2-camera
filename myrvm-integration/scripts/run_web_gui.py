#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from installation_method.web_config_gui.app import app, socketio  # type: ignore

def main() -> None:
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()


