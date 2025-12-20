#!/usr/bin/env bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "[SETUP] Cartella progetto: $BASE_DIR"

# Controllo python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "[SETUP] ERRORE: python3 non trovato. Installa Python 3 prima di procedere."
  exit 1
fi

# Crea venv se non esiste
if [ ! -d "venv" ]; then
  echo "[SETUP] Creo virtualenv in ./venv"
  python3 -m venv venv
else
  echo "[SETUP] Virtualenv già presente in ./venv"
fi

# Attiva venv
# shellcheck disable=SC1091
source venv/bin/activate

echo "[SETUP] Aggiorno pip e installo dipendenze da requirements.txt"
pip install --upgrade pip
pip install -r requirements.txt

echo "[SETUP] Completato."
