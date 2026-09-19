#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "File .env mancante."
  exit 1
fi

set -a
. ./.env
set +a

docker compose ps

echo
echo "Mautic:"
if curl -fsS "http://${MAUTIC_BIND:-127.0.0.1}:${MAUTIC_PORT:-8793}/" >/dev/null; then
  echo "  OK"
else
  echo "  NON RAGGIUNGIBILE"
fi

echo "GE360 Bridge:"
curl -fsS "http://${GE360_BRIDGE_BIND:-127.0.0.1}:${GE360_BRIDGE_PORT:-8794}/health" || true
echo
