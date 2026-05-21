#!/usr/bin/env bash
# Dev server con logging verboso para no quedarnos ciegos cuando algo falla.
#
# Uso:
#   ./dev.sh                  # LOG_LEVEL=DEBUG, escucha en LAN (0.0.0.0)
#   ./dev.sh --verbose-libs   # también muestra httpx/sqlalchemy en DEBUG

set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d venv ]]; then
  echo "venv no existe — corre: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source venv/bin/activate

export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"

# 0.0.0.0 permite que Expo Go (en el teléfono) llegue al backend por LAN.
exec uvicorn api.app:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level debug \
  --access-log
