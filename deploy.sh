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
echo "Деплой успешно завершён"
