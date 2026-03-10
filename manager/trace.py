"""EN: Structured client trace manager for reproducible Telegram verification diagnostics.
RU: Менеджер структурированной клиентской трассировки для воспроизводимой диагностики Telegram-верификации.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    """EN: Return current UTC timestamp in ISO-8601 with milliseconds.
    RU: Вернуть текущий UTC timestamp в ISO-8601 с миллисекундами.
    """

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe_bool(value: Any) -> bool:
    """EN: Convert value to boolean without raising exceptions.
    RU: Преобразовать значение в boolean без выброса исключений.
    """

    try:
        return bool(value)
    except Exception:
        return False


@dataclass(frozen=True)
class _TracePaths:
    """EN: Filesystem paths for one trace run.
    RU: Пути файловой системы для одного запуска трассировки.
    """

    root: Path
    client_trace_jsonl: Path
    client_trace_summary: Path
    env_snapshot: Path
    http_trace_jsonl: Path
    open_trace_jsonl: Path


class TraceManager:
    """EN: Singleton-like trace writer that stores structured JSONL + summary text.
    RU: Псевдо-singleton writer трассировки, сохраняющий структурный JSONL + текстовый summary.
    """

    _instance: "TraceManager | None" = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls) -> "TraceManager":
        """EN: Return initialized singleton instance.
        RU: Вернуть инициализированный singleton-экземпляр.
        """

        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        """EN: Build trace directory layout and initialize writers.
        RU: Создать структуру директории трассировки и инициализировать writers.
        """

        self._enabled = str(os.getenv("TRACE_ENABLE", "0")).strip() in {"1", "true", "True", "yes", "YES"}
        self._seq = 0
        self._write_lock = threading.Lock()
        self._paths = self._resolve_paths()
        self._ensure_dirs()
        self._write_env_snapshot()

    def _resolve_paths(self) -> _TracePaths:
        """EN: Resolve output paths from TRACE_DIR or default logs/trace/<timestamp>.
        RU: Определить выходные пути из TRACE_DIR или по умолчанию logs/trace/<timestamp>.
        """

        explicit_dir = str(os.getenv("TRACE_DIR", "")).strip()
        if explicit_dir:
            root = Path(explicit_dir)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            root = Path("logs") / "trace" / stamp
        return _TracePaths(
            root=root,
            client_trace_jsonl=root / "client_trace.jsonl",
            client_trace_summary=root / "client_trace_summary.log",
            env_snapshot=root / "env_snapshot.txt",
            http_trace_jsonl=root / "http_trace.jsonl",
            open_trace_jsonl=root / "open_trace.jsonl",
        )

    def _ensure_dirs(self) -> None:
        """EN: Ensure trace root directory exists.
        RU: Убедиться, что корневая директория трассировки существует.
        """

        self._paths.root.mkdir(parents=True, exist_ok=True)
        if self._enabled:
            for file_path in (
                self._paths.client_trace_jsonl,
                self._paths.client_trace_summary,
                self._paths.http_trace_jsonl,
                self._paths.open_trace_jsonl,
            ):
                file_path.touch(exist_ok=True)

    @property
    def enabled(self) -> bool:
        """EN: Return current trace-enabled flag.
        RU: Вернуть текущий флаг включенной трассировки.
        """

        return self._enabled

    @property
    def root_dir(self) -> Path:
        """EN: Return trace root directory path.
        RU: Вернуть путь корневой директории трассировки.
        """

        return self._paths.root

    def mask_token(self, token: str) -> str:
        """EN: Mask token as first4...last4(len=N) to avoid sensitive leakage.
        RU: Маскировать токен как first4...last4(len=N), чтобы избежать утечки чувствительных данных.
        """

        value = str((token or "").strip())
        if not value:
            return "<empty>"
        if len(value) <= 8:
            return f"{'*' * len(value)}(len={len(value)})"
        return f"{value[:4]}...{value[-4:]}(len={len(value)})"

    def mask_code(self, code: str) -> str:
        """EN: Mask code value with edge-only view or hidden representation.
        RU: Маскировать code со view только краев или скрытым представлением.
        """

        value = str((code or "").strip())
        if not value:
            return "<empty>"
        if len(value) <= 4:
            return f"{'*' * len(value)}(len={len(value)})"
        return f"{value[:2]}...{value[-2:]}(len={len(value)})"

    def _sanitize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """EN: Sanitize event data to avoid leaking secrets.
        RU: Санитизировать данные события для исключения утечки секретов.
        """

        out: dict[str, Any] = {}
        for key, value in (data or {}).items():
            low_key = str(key).lower()
            if any(x in low_key for x in ("password", "jwt_secret", "reset_secret")):
                out[key] = "<redacted>"
                continue
            if any(x in low_key for x in ("access_token", "refresh_token", "authorization", "token")):
                out[key] = self.mask_token(str(value))
                continue
            if any(x in low_key for x in ("code", "start")) and isinstance(value, str):
                out[key] = self.mask_code(value)
                continue
            out[key] = value
        return out

    def _next_seq(self) -> int:
        """EN: Allocate next monotonic event sequence number.
        RU: Выделить следующий монотонный sequence-номер события.
        """

        self._seq += 1
        return self._seq

    def _write_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        """EN: Append one JSON object line to target JSONL file.
        RU: Добавить одну JSON-строку в целевой JSONL-файл.
        """

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _write_summary_line(self, line: str) -> None:
        """EN: Append one human-readable line to summary log.
        RU: Добавить одну читаемую строку в summary-log.
        """

        with self._paths.client_trace_summary.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def log(self, cat: str, name: str, lvl: str = "INFO", **data: Any) -> None:
        """EN: Write one structured trace event.
        RU: Записать одно структурированное trace-событие.
        """

        if not self._enabled:
            return
        event_data = self._sanitize_data(data)
        with self._write_lock:
            seq = self._next_seq()
            event = {
                "ts": _utc_now_iso(),
                "seq": seq,
                "lvl": str(lvl or "INFO"),
                "cat": str(cat or "STATE"),
                "name": str(name or "event"),
                "data": event_data,
            }
            self._write_jsonl(self._paths.client_trace_jsonl, event)
            if str(cat).upper() == "HTTP":
                self._write_jsonl(self._paths.http_trace_jsonl, event)
            if str(cat).upper() in {"OPEN", "TIMER"}:
                self._write_jsonl(self._paths.open_trace_jsonl, event)
            self._write_summary_line(
                f"#{seq} {event['ts']} {event['lvl']} {event['cat']} {event['name']} data={event_data}"
            )

    def exception(self, cat: str, name: str, exc: BaseException, **data: Any) -> None:
        """EN: Write structured exception event with stacktrace string.
        RU: Записать структурированное exception-событие со stacktrace-строкой.
        """

        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.log(cat=cat, name=name, lvl="ERROR", exc_type=type(exc).__name__, exc=str(exc), stacktrace=stack, **data)

    def flush(self) -> None:
        """EN: Compatibility no-op flush for file-per-write implementation.
        RU: Совместимый no-op flush для реализации с записью файла на каждое событие.
        """

        return

    def _write_env_snapshot(self) -> None:
        """EN: Save safe environment snapshot used for one trace run.
        RU: Сохранить безопасный snapshot окружения для одного запуска трассировки.
        """

        if not self._enabled:
            return
        from manager.config import API_BASE_URL, TELEGRAM_BOT_USERNAME, TG_OPEN_TIMEOUT_SEC, TG_VERIFY_TIMEOUT_SEC
        from data.user_cache.user_cache_reader import get_user_cache

        cache = get_user_cache() or {}
        user_id = cache.get("user_id")
        access_present = _safe_bool(str((cache.get("access_token") or "").strip()))
        refresh_present = _safe_bool(str((cache.get("refresh_token") or "").strip()))

        lines = [
            f"ts={_utc_now_iso()}",
            f"platform={platform.platform()}",
            f"sys_platform={sys.platform}",
            f"python={sys.version.split()[0]}",
            f"API_BASE_URL={API_BASE_URL}",
            f"TELEGRAM_BOT_USERNAME={TELEGRAM_BOT_USERNAME}",
            f"TG_OPEN_TIMEOUT_SEC={TG_OPEN_TIMEOUT_SEC}",
            f"TG_VERIFY_TIMEOUT_SEC={TG_VERIFY_TIMEOUT_SEC}",
            f"user_id={user_id}",
            f"access_token_present={access_present}",
            f"refresh_token_present={refresh_present}",
        ]
        self._paths.env_snapshot.write_text("\n".join(lines) + "\n", encoding="utf-8")


def trace_log(cat: str, name: str, lvl: str = "INFO", **data: Any) -> None:
    """EN: Convenience wrapper for TraceManager.instance().log(...).
    RU: Удобная обертка для TraceManager.instance().log(...).
    """

    TraceManager.instance().log(cat=cat, name=name, lvl=lvl, **data)


def trace_exception(cat: str, name: str, exc: BaseException, **data: Any) -> None:
    """EN: Convenience wrapper for TraceManager.instance().exception(...).
    RU: Удобная обертка для TraceManager.instance().exception(...).
    """

    TraceManager.instance().exception(cat=cat, name=name, exc=exc, **data)
