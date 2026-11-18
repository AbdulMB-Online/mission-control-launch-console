#!/bin/sh
set -eu
cd /workspace/frontend
npm test
npm run build
cd /workspace/backend
python -m pytest
