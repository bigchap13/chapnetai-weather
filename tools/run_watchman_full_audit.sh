#!/data/data/com.termux/files/usr/bin/bash
set -e
cd ~/chapnetai-weather || exit 1

python -m py_compile app.py watchman_knowledge/*.py

pkill -f "python.*app.py" 2>/dev/null || true
sleep 1
nohup python app.py > logs/chapnetai_weather.log 2>&1 &
sleep 4

python tools/watchman_full_audit.py
