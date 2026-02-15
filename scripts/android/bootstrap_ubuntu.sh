#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y \
  git zip unzip \
  python3 python3-pip python3-venv python3-virtualenv \
  openjdk-17-jdk \
  autoconf libtool libtool-bin pkg-config \
  zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 \
  cmake libffi-dev libssl-dev \
  automake autopoint gettext \
  curl

if ! command -v rustup >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi

# shellcheck disable=SC1090
source "$HOME/.cargo/env"

echo "python3: $(python3 --version)"
echo "pip: $(python3 -m pip --version)"
echo "java: $(java -version 2>&1 | head -n 1)"
echo "javac: $(javac -version 2>&1)"
echo "rustc: $(rustc --version)"
echo "cargo: $(cargo --version)"