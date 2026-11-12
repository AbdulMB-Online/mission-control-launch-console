FROM node:22-bookworm-slim@sha256:5ec23b7c622b00547753bc6ffd78085dd868a68aeb41c8e0a1418f033e13d96d AS node
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
WORKDIR /workspace
COPY backend/requirements-dev.lock /tmp/requirements-dev.lock
RUN pip install --no-cache-dir -r /tmp/requirements-dev.lock
COPY frontend/package*.json /workspace/frontend/
RUN npm --prefix frontend ci --no-audit --no-fund
COPY backend /workspace/backend
COPY frontend /workspace/frontend
COPY scripts/test.sh /workspace/scripts/test.sh
ENV LLM_PROVIDER=fake DATABASE_URL=sqlite+aiosqlite:////tmp/mission-test.sqlite
CMD ["sh", "/workspace/scripts/test.sh"]
