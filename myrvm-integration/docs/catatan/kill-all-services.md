bash -lc "source ~/.bashrc 2>/dev/null || true; \
if [ -n \"${RVM_SUDO_PASS:-}\" ]; then echo \"$RVM_SUDO_PASS\" | sudo -S /usr/bin/systemctl stop rvm-remote-camera.service rvm-remote-gui.service rvm-remote-access.service | cat || true; else sudo -n /usr/bin/systemctl stop rvm-remote-camera.service rvm-remote-gui.service rvm-remote-access.service | cat || true; fi; \
fuser -k 5000/tcp || true; fuser -k 5001/tcp || true; fuser -k 5002/tcp || true; fuser -k 8080/tcp || true; \
lsof -nP -iTCP:5000,5001,5002,8080 -sTCP:LISTEN | cat || true"