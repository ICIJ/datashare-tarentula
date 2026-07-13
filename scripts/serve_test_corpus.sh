#!/usr/bin/env bash
# Serve an already-indexed test corpus (see seed_test_corpus.sh) in a local
# Datashare web UI. No SCAN/INDEX stages: it only opens the existing index.
#
# Usage: scripts/serve_test_corpus.sh
#   DATA_DIR, PROJECT, PORT env vars override the defaults below.
set -euo pipefail

DATA_DIR="${DATA_DIR:-$HOME/datasets/test-corpus}"
PROJECT="${PROJECT:-test-corpus}"
PORT="${PORT:-8080}"

if curl -sf "localhost:$PORT" >/dev/null 2>&1; then
    echo "Something already listens on :$PORT."
    echo "If it is Datashare, its ES already serves the index; either browse"
    echo "http://localhost:$PORT or stop it and rerun this script to open it"
    echo "on project '$PROJECT'. Or rerun with PORT=8081."
    exit 1
fi

echo ">> serving project '$PROJECT' at http://localhost:$PORT"
exec datashare \
    --defaultProject "$PROJECT" \
    --dataDir "$DATA_DIR" \
    --tcpListenPort "$PORT"
