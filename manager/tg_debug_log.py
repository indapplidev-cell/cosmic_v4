"""EN: Unified Telegram debug logger for deterministic step tracing.
RU: Единый Telegram debug-логгер для детерминированной трассировки шагов.
"""

from __future__ import annotations

from kivy.logger import Logger
from manager.trace import trace_log


def tglog(msg: str) -> None:
    """EN: Emit Telegram debug line to stdout and logger with flush.
    RU: Вывести строку Telegram debug в stdout и logger с flush.
    """

    text = str(msg)
    print(text, flush=True)
    if text.startswith("[TGDBG] "):
        safe = "TGDBG: " + text[len("[TGDBG] ") :]
    else:
        safe = "TGDBG: " + text
    Logger.info(safe)
    trace_log("STATE", "TGDBG_LINE", raw=text, logger_line=safe)
