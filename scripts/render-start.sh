#!/bin/bash
PORT="${PORT:-10000}"

echo "=========================================="
echo "[RENDER] Iniciando SecOps Universal"
echo "[RENDER] Puerto: ${PORT}"
echo "=========================================="

exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --log-level info
