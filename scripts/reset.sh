#!/usr/bin/env bash
# Wipes the FAISS vector store and rebuilds it from scratch.
# Usage: bash scripts/reset.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[reset] Removing vector store..."
rm -rf "$ROOT/data/vector_store"

echo "[reset] Rebuilding index..."
cd "$ROOT"
python src/ingest.py

echo "[reset] Done."
