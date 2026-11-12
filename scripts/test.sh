#!/bin/sh
set -eu
cd /workspace/backend
python -m pytest
cd /workspace/frontend
npm test
npm run build
