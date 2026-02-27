#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Virtualenv not found at .venv/bin/python"
  echo "Create it first with: python3 -m venv .venv"
  exit 1
fi

LOG_FILE="logs/holistic_tracker.log"
mkdir -p logs
echo "Logging to ${LOG_FILE}"

exec .venv/bin/python game/AvatarStream/scripts/python/holistic_tracker.py \
  --pick-camera \
  --debug \
  --no-virtual-cam \
  --listen-http \
  --listen-host 127.0.0.1 \
  --listen-port 40074 \
  --listen-path /pose \
  --transport none \
  --log-file "${LOG_FILE}"
