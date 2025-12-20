#!/usr/bin/env bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Attiva venv
# shellcheck disable=SC1091
source venv/bin/activate

# Avvia il server Flask
export FLASK_APP=app.server

echo "[RUN] Avvio server AI 3D su 0.0.0.0:5000"
python -m flask run --host=0.0.0.0 --port=5000
