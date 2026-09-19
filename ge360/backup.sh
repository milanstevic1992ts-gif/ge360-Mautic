#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "File .env mancante. Esegui prima ./install.sh"
  exit 1
fi

set -a
. ./.env
set +a

stamp="$(date +%Y%m%d-%H%M%S)"
dest="backups/$stamp"
mkdir -p "$dest"

echo "Backup database..."
docker compose exec -T db sh -lc 'mysqldump --single-transaction --quick --lock-tables=false -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' | gzip > "$dest/mautic.sql.gz"

echo "Backup file persistenti..."
tar -czf "$dest/runtime.tar.gz" runtime

cat > "$dest/manifest.txt" <<EOF
created_at=$(date -Iseconds)
mautic_image=$MAUTIC_IMAGE
compose_project=$COMPOSE_PROJECT_NAME
EOF

echo "Backup completato: $dest"
