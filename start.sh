#!/bin/bash
# 申城智行一键启动（后端+前端静态托管，端口8000）
cd "$(dirname "$0")/backend"
fuser -k 8000/tcp 2>/dev/null
sleep 1
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/shencheng-backend.log 2>&1 &
echo "申城智行已启动: http://localhost:8000  (日志: /tmp/shencheng-backend.log)"
