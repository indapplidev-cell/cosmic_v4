#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs/phone
adb logcat -c

out_file="logs/phone/logcat_$(date +%Y%m%d_%H%M%S).txt"
echo "Writing logcat to: $out_file"
adb logcat -v time | tee "$out_file"
