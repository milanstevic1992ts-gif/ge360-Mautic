#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker non trovato. Installa Docker Engine + Docker Compose plugin e rilancia."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Il plugin 'docker compose' non e disponibile."
  exit 1
fi

[ -f .env ] || cp .env.example .env
[ -f .mautic_env ] || cp .mautic_env.example .mautic_env

make_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(24))
PY
  fi
}

set_if_empty() {
  local key="$1"
  local value="$2"
  if grep -q "^$key=$" .env; then
    sed -i "s|^$key=$|$key=$value|" .env
  fi
}

set_if_empty MYSQL_PASSWORD "$(make_secret)"
set_if_empty MYSQL_ROOT_PASSWORD "$(make_secret)"
set_if_empty GE360_BRIDGE_TOKEN "$(make_secret)"

mkdir -p runtime/config runtime/logs runtime/media/files runtime/media/images backups

echo "Avvio GE360 Mautic..."
if ! docker compose up -d --build; then
  echo
  echo "ERRORE: lo stack non si e avviato correttamente."
  echo "Stato container:"
  docker compose ps || true
  echo
  echo "Ultimi log MySQL:"
  docker compose logs --tail=120 db || true
  exit 1
fi

echo
echo "GE360 Mautic avviato."
echo "UI Mautic:  http://127.0.0.1:$(grep '^MAUTIC_PORT=' .env | cut -d= -f2)"
echo "Bridge:     http://127.0.0.1:$(grep '^GE360_BRIDGE_PORT=' .env | cut -d= -f2)/health"
echo
echo "Dopo la prima configurazione Mautic: Settings -> Plugins -> Install/Upgrade Plugins."
