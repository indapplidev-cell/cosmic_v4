#!/usr/bin/env bash
set -euo pipefail

required_files=(
  /app/server/app/api/main.py
  /app/server/engine/modes/survive_timed/campaign_progress_manager.py
  /app/server/engine/modes/survive_timed/level_result_manager.py
  /app/server/engine/modes/survive_timed/level_success_manager.py
  /app/shared/contracts/survive_timed.py
  /app/shared/constants/survive_timed_levels.py
)

for path in "${required_files[@]}"; do
  [[ -f "$path" ]]
done

python - <<'PY'
import importlib

importlib.import_module("server.app.api.main")
importlib.import_module("shared.constants.survive_timed_levels")
print("imports ok")
PY

for old_path in \
  /app/server/infra \
  /app/server/services \
  /app/server/api/main.py \
  /app/engine
do
  [[ ! -e "$old_path" ]]
done

echo "verify_runtime: pass"
