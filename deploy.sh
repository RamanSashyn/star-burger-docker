#!/usr/bin/env bash
set -euo pipefail

cd /opt/star-burger

echo "[1/5] git pull"
git pull --rebase

echo "[2/5] build & up"
docker compose build
docker compose up -d

echo "[3/5] migrate"
docker compose exec -T backend python manage.py migrate --noinput

echo "[4/5] collectstatic"
docker compose exec -T backend python manage.py collectstatic --noinput

echo "[5/5] nginx reload (хост)"
sudo nginx -t && sudo systemctl reload nginx

echo "OK"
