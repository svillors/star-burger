#!/bin/bash

set -e
git pull
if [ ! -d "venvasd" ]; then
    python3 -m venv venvasd
fi
docker compose build
docker compose run --rm frontend
docker compose up -d database
docker compose up -d backend
sudo systemctl reload nginx.service
sudo systemctl restart star-burger.service
source .env
REVISION=$(git rev-parse HEAD)
USERNAME=$(whoami)
curl -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d "{\"environment\": \"production\", \"revision\": \"$REVISION\", \"local_username\": \"$USERNAME\"}"
echo "Деплой успешно завершён"
