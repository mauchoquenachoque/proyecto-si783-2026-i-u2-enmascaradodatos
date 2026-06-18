#!/bin/bash

set -e

echo "Starting masking_service..."
uvicorn masking_service:app \
--host 0.0.0.0 \
--port 8001 \
--log-level warning &

echo "Starting monitor_service..."
uvicorn monitor_service:app \
--host 0.0.0.0 \
--port 8002 \
--log-level warning &

sleep 5

echo "Starting main API..."
exec uvicorn main:app \
--host 0.0.0.0 \
--port ${PORT} \
--log-level info
