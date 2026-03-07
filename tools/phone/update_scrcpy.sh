#!/usr/bin/env bash
set -euo pipefail

apt-get update -y >/dev/null
apt-get install -y curl jq tar >/dev/null

rel_json="$(curl -fsSL https://api.github.com/repos/Genymobile/scrcpy/releases/latest)"
tag="$(printf '%s' "$rel_json" | jq -r '.tag_name')"
url="$(printf '%s' "$rel_json" | jq -r '.assets[].browser_download_url' | grep -E 'scrcpy-linux-x86_64-.*\.tar\.gz$' | head -n1)"

if [[ -z "${url:-}" ]]; then
  echo "ERROR: linux x86_64 scrcpy asset not found in latest release" >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p /opt/scrcpy
curl -fL "$url" -o "$tmp_dir/scrcpy.tgz"
rm -rf /opt/scrcpy/current
mkdir -p /opt/scrcpy/current
tar -xzf "$tmp_dir/scrcpy.tgz" -C /opt/scrcpy/current --strip-components=1
ln -sf /opt/scrcpy/current/scrcpy /usr/local/bin/scrcpy
chmod +x /usr/local/bin/scrcpy

echo "Installed scrcpy release: $tag"
scrcpy --version | head -n 8
