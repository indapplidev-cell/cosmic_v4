#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

rm -rf "$ROOT_DIR/.buildozer" "$ROOT_DIR/bin"

# EN: Remove common temporary build artifacts.
# RU: Удаляет типовые временные артефакты сборки.
find "$ROOT_DIR" -maxdepth 3 -type d \( -name "__pycache__" -o -name ".gradle" \) -prune -exec rm -rf {} + || true

echo "Clean complete"