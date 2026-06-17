#!/bin/sh
set -e

PORT="${PORT:-10000}"

echo "[RENDER] Iniciando los 3 servicios..."
echo "[RENDER] Monitor Service en puerto 8002"
echo "[RENDER] Masking Service en puerto 8001"
echo "[RENDER] API Principal en puerto ${PORT}"

# Iniciar Monitor Service en segundo plano
uvicorn monitor_service:app --host 0.0.0.0 --port 8002 &
MONITOR_PID=$!

# Iniciar Masking Service en segundo plano
uvicorn masking_service:app --host 0.0.0.0 --port 8001 &
MASKING_PID=$!

# Esperar un momento para que los servicios inicien
sleep 3

# Iniciar API Principal (este es el que Render monitorea)
exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
