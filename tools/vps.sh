#!/usr/bin/env bash
set -euo pipefail

SERVER_IP=185.216.87.26
SERVER_USER=root
KEY_PATH=$HOME/.ssh/cosmic_vps_ed25519
SSH_OPTS="-o BatchMode=yes -o StrictHostKeyChecking=accept-new -i $KEY_PATH"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_ROOT="$PROJECT_ROOT/logs/vps"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$LOGS_ROOT/$TIMESTAMP"

mkdir -p "$RUN_DIR"

run_remote_to_file() {
  local outfile="$1"
  local remote_cmd="$2"
  local outpath="$RUN_DIR/$outfile"

  echo "[run] $remote_cmd"
  if ssh $SSH_OPTS "${SERVER_USER}@${SERVER_IP}" "bash -lc $(printf '%q' "$remote_cmd")" >"$outpath" 2>&1; then
    echo "[ok]  $outpath"
  else
    echo "[err] $outpath"
    return 1
  fi
}

run_remote_allow_fail() {
  local outfile="$1"
  local remote_cmd="$2"
  local outpath="$RUN_DIR/$outfile"

  echo "[run] $remote_cmd"
  if ssh $SSH_OPTS "${SERVER_USER}@${SERVER_IP}" "bash -lc $(printf '%q' "$remote_cmd")" >"$outpath" 2>&1; then
    echo "[ok]  $outpath"
  else
    echo "[warn] command failed, output saved: $outpath"
  fi
}

check_key() {
  if [[ ! -f "$KEY_PATH" ]]; then
    echo "ERROR: SSH key not found: $KEY_PATH" >&2
    exit 1
  fi
}

sub_cmd() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: bash tools/vps.sh cmd \"<command>\"" >&2
    exit 1
  fi
  local user_cmd="$1"
  printf '%s\n' "$user_cmd" >"$RUN_DIR/command.txt"
  run_remote_to_file "cmd.out.txt" "$user_cmd"
}

sub_diag() {
  run_remote_to_file "whoami_id.txt" "whoami; id"
  run_remote_to_file "os.txt" "uname -a; cat /etc/os-release || true"
  run_remote_to_file "net.txt" "ip a; ip r"
  run_remote_to_file "ports.txt" "ss -lntup | head -n 200"
  run_remote_to_file "docker.txt" "docker --version || true; docker compose version || true; docker ps || true"
  run_remote_to_file "firewall.txt" "ufw status verbose || true; iptables -S | head -n 120 || true"
}

sub_docker_ps() {
  run_remote_to_file "docker_ps.txt" "docker ps"
}

sub_docker_logs() {
  if [[ $# -lt 1 ]]; then
    echo "Usage: bash tools/vps.sh docker-logs <container> [--tail N]" >&2
    exit 1
  fi

  local container="$1"
  shift
  local tail_n=300
  if [[ $# -ge 2 && "$1" == "--tail" ]]; then
    tail_n="$2"
  fi

  run_remote_allow_fail "docker_logs_${container}.txt" "docker logs --tail $tail_n $container"
}

sub_engine_crash() {
  run_remote_allow_fail "engine_ps_a.txt" "docker ps -a --filter name=gamecom-engine"
  run_remote_allow_fail "engine_inspect.json" "docker inspect gamecom-engine"
  run_remote_allow_fail "engine_logs_tail300.txt" "docker logs --tail 300 gamecom-engine"
  run_remote_allow_fail "db_logs_tail300.txt" "docker logs --tail 300 gamecom-db"
  run_remote_to_file "ports.txt" "ss -lntup | head -n 200"
  run_remote_to_file "disk_df_h.txt" "df -h"
}

sub_push_file() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: bash tools/vps.sh push-file <local_file> <remote_file>" >&2
    exit 1
  fi
  local local_file="$1"
  local remote_file="$2"
  local outpath="$RUN_DIR/push_file.txt"

  if [[ ! -f "$local_file" ]]; then
    echo "ERROR: local file not found: $local_file" | tee "$outpath" >&2
    exit 1
  fi

  echo "[run] push-file $local_file -> $remote_file" | tee "$outpath"
  local remote_dir
  remote_dir="$(dirname "$remote_file")"
  if ssh $SSH_OPTS "${SERVER_USER}@${SERVER_IP}" "mkdir -p $(printf '%q' "$remote_dir")" >>"$outpath" 2>&1; then
    if cat "$local_file" | ssh $SSH_OPTS "${SERVER_USER}@${SERVER_IP}" "cat > $(printf '%q' "$remote_file")" >>"$outpath" 2>&1; then
      echo "[ok]  $outpath" | tee -a "$outpath"
    else
      echo "[err] $outpath" | tee -a "$outpath"
      return 1
    fi
  else
    echo "[err] $outpath" | tee -a "$outpath"
    return 1
  fi
}

sub_sync_dir() {
  if [[ $# -ne 2 ]]; then
    echo "Usage: bash tools/vps.sh sync-dir <local_dir> <remote_dir>" >&2
    exit 1
  fi
  local local_dir="$1"
  local remote_dir="$2"
  local outpath="$RUN_DIR/sync_dir.txt"

  if [[ ! -d "$local_dir" ]]; then
    echo "ERROR: local dir not found: $local_dir" | tee "$outpath" >&2
    exit 1
  fi

  echo "[run] sync-dir $local_dir -> $remote_dir" | tee "$outpath"
  if tar -C "$local_dir" -cf - . | ssh $SSH_OPTS "${SERVER_USER}@${SERVER_IP}" "mkdir -p $(printf '%q' "$remote_dir") && tar -C $(printf '%q' "$remote_dir") -xf -" >>"$outpath" 2>&1; then
    echo "[ok]  $outpath" | tee -a "$outpath"
  else
    echo "[err] $outpath" | tee -a "$outpath"
    return 1
  fi
}

usage() {
  cat <<'EOF'
Usage:
  bash tools/vps.sh cmd "<command>"
  bash tools/vps.sh diag
  bash tools/vps.sh docker-ps
  bash tools/vps.sh docker-logs <container> [--tail N]
  bash tools/vps.sh engine-crash
  bash tools/vps.sh push-file <local_file> <remote_file>
  bash tools/vps.sh sync-dir <local_dir> <remote_dir>
EOF
}

main() {
  check_key

  if [[ $# -lt 1 ]]; then
    usage
    exit 1
  fi

  local sub="$1"
  shift
  case "$sub" in
    cmd) sub_cmd "$@" ;;
    diag) sub_diag ;;
    docker-ps) sub_docker_ps ;;
    docker-logs) sub_docker_logs "$@" ;;
    engine-crash) sub_engine_crash ;;
    push-file) sub_push_file "$@" ;;
    sync-dir) sub_sync_dir "$@" ;;
    *) usage; exit 1 ;;
  esac

  echo "Report directory: $RUN_DIR"
}

main "$@"
