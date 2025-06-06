#!/bin/bash

set -e
git pull
if [ ! -d "venvasd" ]; then
    python3 -m venv venvasd
fi
venvasd/bin/pip install -r requirements.txt
npm ci --dev
python3 manage.py migrate
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python3 manage.py collectstatic --noinput
sudo systemctl reload nginx.service
sudo systemctl restart star-burger.service
source .env
REVISION=$(git rev-parse HEAD)
USERNAME=$(whoami)
curl -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d "{\"environment\": \"production\", \"revision\": \"$REVISION\", \"local_username\": \"$USERNAME\"}"
echo "Деплой успешно завершён"
