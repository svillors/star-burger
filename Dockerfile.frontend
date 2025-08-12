FROM node:16.16.0-slim

WORKDIR /app/

COPY package-lock.json ./package-lock.json
COPY package.json ./package.json
RUN npm ci

COPY bundles-src ./bundles-src/
COPY assets/ ./assets/

CMD ["npx","parcel","build","bundles-src/index.js","--dist-dir","/app/staticfiles","--public-url","/staticfiles"]

