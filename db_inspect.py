"""EN: Read-only DB inspector for real-time remote VPS database (SSH mode only).
RU: Read-only инспектор БД для данных удалённого VPS в реальном времени (только SSH-режим).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shlex
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


console = Console()

REMOTE_HOST_DEFAULT = os.getenv("DB_INSPECT_REMOTE_HOST", "185.216.87.26")
REMOTE_USER_DEFAULT = os.getenv("DB_INSPECT_REMOTE_USER", "root")
REMOTE_CONTAINER_DEFAULT = os.getenv("DB_INSPECT_REMOTE_CONTAINER", "infra-api-1")
REMOTE_KEY_DEFAULT = os.getenv("DB_INSPECT_REMOTE_KEY", str(Path.home() / ".ssh" / "cosmic_vps_ed25519"))
COMPOSE_FILE_DEFAULT = os.getenv("DB_INSPECT_COMPOSE_FILE", "server/infra/docker-compose.yml")
COMPOSE_ENV_FILE_DEFAULT = os.getenv("DB_INSPECT_COMPOSE_ENV_FILE", "server/.env")
COMPOSE_API_SERVICE_DEFAULT = os.getenv("DB_INSPECT_COMPOSE_API_SERVICE", "api")


def find_project_root(start: Path) -> Path:
    """EN: Find project root by locating server/config.py or server/db.py.
    RU: Найти корень проекта по наличию server/config.py или server/db.py.
    """
    for candidate in [start, *start.parents]:
        server_dir = candidate / "server"
        if (server_dir / "config.py").exists() or (server_dir / "db.py").exists():
            return candidate

    console.print(
        "[bold red]ERROR:[/bold red] Project root not found. "
        "Expected server/config.py or server/db.py in current/parent directories."
    )
    raise SystemExit(1)


PROJECT_ROOT = find_project_root(Path(__file__).resolve().parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _read_server_database_url() -> str:
    """EN: Try to read DATABASE_URL from server.config; return empty on failure.
    RU: Попытаться прочитать DATABASE_URL из server.config; при ошибке вернуть пустую строку.
    """
    try:
        from server.config import DATABASE_URL as cfg_url  # noqa: WPS433

        return (cfg_url or "").strip()
    except Exception:
        return ""


def _parse_args() -> argparse.Namespace:
    """EN: Parse command line arguments for the DB inspector.
    RU: Разобрать аргументы командной строки для инспектора БД.
    """
    parser = argparse.ArgumentParser(
        description="Inspect PostgreSQL tables/columns and print sample rows (read-only)."
    )
    parser.add_argument("--table", help="Show only one table by name.")
    parser.add_argument("--limit", type=int, default=50, help="Rows per table (default: 50).")
    parser.add_argument("--schema", default=None, help="Schema name (PostgreSQL).")
    parser.add_argument(
        "--no-rows",
        action="store_true",
        help="Show only table structures, skip row data.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print rows as dictionaries for debugging.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Explicit DB URL for local mode.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Force local SQLAlchemy mode (disable SSH remote mode).",
    )
    parser.add_argument(
        "--compose",
        action="store_true",
        help="Force docker compose mode (inspect via api container).",
    )
    parser.add_argument(
        "--compose-file",
        default=COMPOSE_FILE_DEFAULT,
        help="Docker compose file path for compose mode.",
    )
    parser.add_argument(
        "--compose-env-file",
        default=COMPOSE_ENV_FILE_DEFAULT,
        help="Docker compose env file path for compose mode.",
    )
    parser.add_argument(
        "--compose-api-service",
        default=COMPOSE_API_SERVICE_DEFAULT,
        help="Docker compose service name where DATABASE_URL is configured.",
    )
    parser.add_argument("--remote-host", default=REMOTE_HOST_DEFAULT, help="SSH host for remote inspect.")
    parser.add_argument("--remote-user", default=REMOTE_USER_DEFAULT, help="SSH user for remote inspect.")
    parser.add_argument("--remote-key", default=REMOTE_KEY_DEFAULT, help="SSH private key path.")
    parser.add_argument(
        "--remote-container",
        default=REMOTE_CONTAINER_DEFAULT,
        help="Docker container on VPS where DATABASE_URL is configured.",
    )
    return parser.parse_args()


def _resolve_database_url(explicit_url: str | None) -> str:
    """EN: Resolve URL with priority: CLI -> env DATABASE_URL -> server config.
    RU: Определить URL с приоритетом: CLI -> env DATABASE_URL -> server config.
    """
    if explicit_url:
        db_url = explicit_url.strip()
    else:
        env_url = os.getenv("DATABASE_URL", "").strip()
        db_url = env_url if env_url else _read_server_database_url()

    return db_url


def _build_engine(db_url: str) -> Engine:
    """EN: Build SQLAlchemy engine from resolved URL.
    RU: Создать SQLAlchemy engine по определённому URL.
    """
    return create_engine(db_url, future=True)


def _render_columns_meta(table_name: str, columns: list[dict]) -> None:
    """EN: Render table columns metadata as a rich table.
    RU: Вывести метаданные колонок таблицы в формате rich-таблицы.
    """
    meta = Table(title=f"{table_name}: columns", show_lines=False)
    meta.add_column("Name", style="cyan", no_wrap=True)
    meta.add_column("Type", style="magenta")
    meta.add_column("Nullable", style="yellow", justify="center")
    meta.add_column("Default", style="green")

    for col in columns:
        meta.add_row(
            str(col.get("name")),
            str(col.get("type")),
            "yes" if bool(col.get("nullable", True)) else "no",
            str(col.get("default")),
        )

    console.print(meta)


def _quote_table(engine_obj: Engine, table_name: str, schema: str | None) -> str:
    """EN: Safely quote table identifier for raw SQL text query.
    RU: Безопасно экранировать идентификатор таблицы для raw SQL text-запроса.
    """
    prep = engine_obj.dialect.identifier_preparer
    if schema:
        return f"{prep.quote_identifier(schema)}.{prep.quote_identifier(table_name)}"
    return prep.quote_identifier(table_name)


def _fetch_rows(
    engine_obj: Engine,
    table_name: str,
    *,
    schema: str | None,
    limit: int,
) -> list[dict]:
    """EN: Read first N rows from a table with bound LIMIT.
    RU: Прочитать первые N строк таблицы с bind-параметром LIMIT.
    """
    quoted = _quote_table(engine_obj, table_name, schema)
    stmt = text(f"SELECT * FROM {quoted} LIMIT :limit")
    with engine_obj.connect() as conn:
        result = conn.execute(stmt, {"limit": limit})
        return [dict(row) for row in result.mappings().all()]


def _iter_tables(engine_obj: Engine, schema: str | None) -> Iterable[str]:
    """EN: Yield table names for selected schema.
    RU: Вернуть имена таблиц выбранной схемы.
    """
    inspector = inspect(engine_obj)
    return inspector.get_table_names(schema=schema)


def _render_rows_table(table_name: str, rows: list[dict], columns: list[str]) -> None:
    """EN: Render row samples as a rich table.
    RU: Вывести выборку строк в формате rich-таблицы.
    """
    if not rows:
        console.print(f"[dim]{table_name}: (0 rows)[/dim]")
        return

    data = Table(title=f"{table_name}: rows ({len(rows)})", show_lines=False)
    for col in columns:
        data.add_column(col, overflow="fold")

    for row in rows:
        data.add_row(*[str(row.get(col)) for col in columns])

    console.print(data)


def _remote_collect(args: argparse.Namespace) -> dict[str, Any]:
    """EN: Collect DB structure/rows on VPS via SSH+docker exec and return JSON.
    RU: Собрать структуру/строки БД на VPS через SSH+docker exec и вернуть JSON.
    """
    script = r'''
import json
import os
from decimal import Decimal
from sqlalchemy import create_engine, inspect, text

schema = os.environ.get("INSPECT_SCHEMA") or None
table = os.environ.get("INSPECT_TABLE") or None
limit = int(os.environ.get("INSPECT_LIMIT", "50"))
no_rows = os.environ.get("INSPECT_NO_ROWS", "0") == "1"

db_url = os.environ.get("DATABASE_URL", "").strip()
if not db_url.startswith("postgresql"):
    print(json.dumps({"ok": False, "error": f"BAD_DATABASE_URL:{db_url}"}))
    raise SystemExit(0)

engine = create_engine(db_url, future=True)
inspector = inspect(engine)
tables = inspector.get_table_names(schema=schema)
if table:
    if table not in tables:
        print(json.dumps({"ok": False, "error": f"TABLE_NOT_FOUND:{table}"}))
        raise SystemExit(0)
    tables = [table]

def quote_table(name: str, sc: str | None) -> str:
    prep = engine.dialect.identifier_preparer
    if sc:
        return f"{prep.quote_identifier(sc)}.{prep.quote_identifier(name)}"
    return prep.quote_identifier(name)

result = {"ok": True, "tables": []}

def to_jsonable(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value

for name in tables:
    cols = inspector.get_columns(name, schema=schema)
    serial_cols = []
    for col in cols:
        serial_cols.append(
            {
                "name": col.get("name"),
                "type": str(col.get("type")),
                "nullable": bool(col.get("nullable", True)),
                "default": str(col.get("default")),
            }
        )
    rec = {"name": name, "columns": serial_cols, "rows": []}
    if not no_rows:
        stmt = text(f"SELECT * FROM {quote_table(name, schema)} LIMIT :limit")
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"limit": limit}).mappings().all()
            rec["rows"] = [
                {key: to_jsonable(value) for key, value in dict(r).items()}
                for r in rows
            ]
    result["tables"].append(rec)

print(json.dumps(result, ensure_ascii=False))
    '''
    b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")

    remote_code = f"import os,base64;exec(base64.b64decode('{b64}'))"
    env_items = {
        "INSPECT_SCHEMA": args.schema or "",
        "INSPECT_TABLE": args.table or "",
        "INSPECT_LIMIT": str(int(args.limit)),
        "INSPECT_NO_ROWS": "1" if args.no_rows else "0",
    }
    remote_parts = ["docker", "exec"]
    for key, value in env_items.items():
        remote_parts.extend(["-e", f"{key}={value}"])
    remote_parts.extend(
        [
            "-i",
            args.remote_container,
            "python",
            "-c",
            remote_code,
        ]
    )
    remote_cmd = " ".join(shlex.quote(part) for part in remote_parts)

    ssh_cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-i",
        args.remote_key,
        f"{args.remote_user}@{args.remote_host}",
        remote_cmd,
    ]
    proc = subprocess.run(ssh_cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or "SSH remote execution failed")

    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError("Remote inspect returned empty output")

    try:
        payload = json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Remote returned non-JSON output: {out[:500]}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected remote payload type: {type(payload)}")
    if payload.get("ok") is not True:
        raise RuntimeError(str(payload.get("error", "REMOTE_ERROR")))
    return payload


def _run_embedded_collect_via_command(
    base_command: list[str],
    args: argparse.Namespace,
    *,
    error_prefix: str,
) -> dict[str, Any]:
    """EN: Run embedded SQLAlchemy collector script through provided command and parse JSON.
    RU: Запустить встроенный SQLAlchemy-коллектор через переданную команду и разобрать JSON.
    """

    script = r'''
import json
import os
from decimal import Decimal
from sqlalchemy import create_engine, inspect, text

schema = os.environ.get("INSPECT_SCHEMA") or None
table = os.environ.get("INSPECT_TABLE") or None
limit = int(os.environ.get("INSPECT_LIMIT", "50"))
no_rows = os.environ.get("INSPECT_NO_ROWS", "0") == "1"

db_url = os.environ.get("DATABASE_URL", "").strip()
if not db_url.startswith("postgresql"):
    print(json.dumps({"ok": False, "error": f"BAD_DATABASE_URL:{db_url}"}))
    raise SystemExit(0)

engine = create_engine(db_url, future=True)
inspector = inspect(engine)
tables = inspector.get_table_names(schema=schema)
if table:
    if table not in tables:
        print(json.dumps({"ok": False, "error": f"TABLE_NOT_FOUND:{table}"}))
        raise SystemExit(0)
    tables = [table]

def quote_table(name: str, sc: str | None) -> str:
    prep = engine.dialect.identifier_preparer
    if sc:
        return f"{prep.quote_identifier(sc)}.{prep.quote_identifier(name)}"
    return prep.quote_identifier(name)

result = {"ok": True, "tables": []}

def to_jsonable(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value

for name in tables:
    cols = inspector.get_columns(name, schema=schema)
    serial_cols = []
    for col in cols:
        serial_cols.append(
            {
                "name": col.get("name"),
                "type": str(col.get("type")),
                "nullable": bool(col.get("nullable", True)),
                "default": str(col.get("default")),
            }
        )
    rec = {"name": name, "columns": serial_cols, "rows": []}
    if not no_rows:
        stmt = text(f"SELECT * FROM {quote_table(name, schema)} LIMIT :limit")
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"limit": limit}).mappings().all()
            rec["rows"] = [
                {key: to_jsonable(value) for key, value in dict(r).items()}
                for r in rows
            ]
    result["tables"].append(rec)

print(json.dumps(result, ensure_ascii=False))
    '''

    b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
    remote_code = f"import base64;exec(base64.b64decode('{b64}'))"
    command = [
        *base_command,
        "python",
        "-c",
        remote_code,
    ]
    env = os.environ.copy()
    env["INSPECT_SCHEMA"] = args.schema or ""
    env["INSPECT_TABLE"] = args.table or ""
    env["INSPECT_LIMIT"] = str(int(args.limit))
    env["INSPECT_NO_ROWS"] = "1" if args.no_rows else "0"

    proc = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip() or f"{error_prefix}: execution failed")

    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError(f"{error_prefix}: empty output")

    try:
        payload = json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{error_prefix}: non-JSON output: {out[:500]}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"{error_prefix}: unexpected payload type {type(payload)}")
    if payload.get("ok") is not True:
        raise RuntimeError(str(payload.get("error", f"{error_prefix}: collector error")))
    return payload


def _compose_collect(args: argparse.Namespace) -> dict[str, Any]:
    """EN: Collect DB structure/rows via docker compose api service (fresh runtime DB config).
    RU: Собрать структуру/строки БД через сервис api в docker compose (актуальная runtime-конфигурация БД).
    """

    compose_file = str((PROJECT_ROOT / args.compose_file).resolve())
    compose_env_file = str((PROJECT_ROOT / args.compose_env_file).resolve())
    base_command = [
        "docker",
        "compose",
        "-f",
        compose_file,
        "--env-file",
        compose_env_file,
        "exec",
        "-T",
        args.compose_api_service,
    ]
    return _run_embedded_collect_via_command(base_command, args, error_prefix="COMPOSE_INSPECT_ERROR")


def _run_local_sqlalchemy(args: argparse.Namespace, db_url: str) -> int:
    """EN: Run local SQLAlchemy inspection path.
    RU: Выполнить локальный путь инспекции через SQLAlchemy.
    """
    if not db_url.startswith("postgresql"):
        console.print(
            f"[bold red]ERROR:[/bold red] PostgreSQL URL required, got: [yellow]{db_url}[/yellow]"
        )
        return 1

    console.print(Panel.fit(f"[bold]Using DB URL:[/bold] {db_url}", border_style="blue"))
    db_engine = _build_engine(db_url)

    try:
        inspector = inspect(db_engine)
        table_names = list(_iter_tables(db_engine, args.schema))
    except Exception as exc:
        console.print(f"[bold red]ERROR:[/bold red] Failed to connect/inspect DB: {exc}")
        return 1

    if args.table:
        if args.table not in table_names:
            console.print(
                f"[bold red]ERROR:[/bold red] Table '{args.table}' not found "
                f"in schema '{args.schema}'."
            )
            return 1
        table_names = [args.table]

    if not table_names:
        console.print("[yellow]No tables found.[/yellow]")
        console.print(f"[dim]cwd: {Path.cwd()}[/dim]")
        console.print("[dim]Hint: python -m alembic -c server/alembic.ini upgrade head[/dim]")
        return 0

    for table_name in table_names:
        console.rule(f"[bold cyan]{table_name}[/bold cyan]")
        try:
            columns = inspector.get_columns(table_name, schema=args.schema)
        except Exception as exc:
            console.print(
                f"[bold red]ERROR:[/bold red] Failed to read columns for {table_name}: {exc}"
            )
            return 1

        _render_columns_meta(table_name, columns)

        if args.no_rows:
            continue

        try:
            rows = _fetch_rows(db_engine, table_name, schema=args.schema, limit=args.limit)
        except Exception as exc:
            console.print(
                f"[bold red]ERROR:[/bold red] Failed to read rows from {table_name}: {exc}"
            )
            return 1

        if args.raw:
            if not rows:
                console.print(f"[dim]{table_name}: (0 rows)[/dim]")
            else:
                for row in rows:
                    console.print(row)
                console.print(f"[dim]({len(rows)} rows)[/dim]")
            continue

        col_names = [str(col.get("name")) for col in columns]
        _render_rows_table(table_name, rows, col_names)

    return 0


def _run_remote(args: argparse.Namespace) -> int:
    """EN: Run remote read-only inspection via SSH and render locally.
    RU: Выполнить удалённую read-only инспекцию по SSH и отрисовать локально.
    """
    console.print(
        Panel.fit(
            f"[bold]Remote mode:[/bold] {args.remote_user}@{args.remote_host} "
            f"container={args.remote_container}",
            border_style="blue",
        )
    )
    try:
        payload = _remote_collect(args)
    except Exception as exc:
        console.print(f"[bold red]ERROR:[/bold red] Remote inspect failed: {exc}")
        return 1

    tables = payload.get("tables", [])
    if not tables:
        console.print("[yellow]No tables found.[/yellow]")
        return 0

    for table in tables:
        table_name = str(table.get("name", "unknown"))
        columns = table.get("columns", []) if isinstance(table.get("columns"), list) else []
        rows = table.get("rows", []) if isinstance(table.get("rows"), list) else []

        console.rule(f"[bold cyan]{table_name}[/bold cyan]")
        _render_columns_meta(table_name, columns)

        if args.no_rows:
            continue

        if args.raw:
            if not rows:
                console.print(f"[dim]{table_name}: (0 rows)[/dim]")
            else:
                for row in rows:
                    console.print(row)
                console.print(f"[dim]({len(rows)} rows)[/dim]")
            continue

        col_names = [str(col.get("name")) for col in columns]
        _render_rows_table(table_name, rows, col_names)

    return 0


def _run_compose(args: argparse.Namespace) -> int:
    """EN: Run inspection via docker compose api container and render output locally.
    RU: Выполнить инспекцию через контейнер api в docker compose и отрисовать вывод локально.
    """

    compose_file = str((PROJECT_ROOT / args.compose_file).resolve())
    compose_env_file = str((PROJECT_ROOT / args.compose_env_file).resolve())
    console.print(
        Panel.fit(
            f"[bold]Compose mode:[/bold] service={args.compose_api_service}\n"
            f"compose_file={compose_file}\n"
            f"env_file={compose_env_file}",
            border_style="blue",
        )
    )
    try:
        payload = _compose_collect(args)
    except Exception as exc:
        console.print(f"[bold red]ERROR:[/bold red] Compose inspect failed: {exc}")
        return 1

    tables = payload.get("tables", [])
    if not tables:
        console.print("[yellow]No tables found.[/yellow]")
        return 0

    for table in tables:
        table_name = str(table.get("name", "unknown"))
        columns = table.get("columns", []) if isinstance(table.get("columns"), list) else []
        rows = table.get("rows", []) if isinstance(table.get("rows"), list) else []

        console.rule(f"[bold cyan]{table_name}[/bold cyan]")
        _render_columns_meta(table_name, columns)

        if args.no_rows:
            continue

        if args.raw:
            if not rows:
                console.print(f"[dim]{table_name}: (0 rows)[/dim]")
            else:
                for row in rows:
                    console.print(row)
                console.print(f"[dim]({len(rows)} rows)[/dim]")
            continue

        col_names = [str(col.get("name")) for col in columns]
        _render_rows_table(table_name, rows, col_names)

    return 0


def main() -> int:
    """EN: CLI entry point for read-only DB inspection.
    RU: Точка входа CLI для read-only инспекции БД.
    """
    args = _parse_args()
    if args.limit <= 0:
        console.print("[bold red]ERROR:[/bold red] --limit must be > 0")
        return 1

    # EN: Remote-only behavior by user requirement: always read from VPS over SSH.
    # RU: Поведение remote-only по требованию пользователя: всегда читать БД с VPS по SSH.
    if args.local or args.compose or args.database_url:
        console.print(
            "[yellow]WARNING:[/yellow] local/compose/database-url options are ignored in remote-only mode."
        )
    return _run_remote(args)


if __name__ == "__main__":
    raise SystemExit(main())
