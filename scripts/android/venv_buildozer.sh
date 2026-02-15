#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv_buildozer"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install -U pip setuptools wheel
python -m pip install buildozer cython==0.29.34

echo "buildozer: $(buildozer --version)"
echo "python: $(python --version)"
echo "pip: $(pip --version)"