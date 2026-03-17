"""EN: Static grep-like check for forbidden raw SQL interpolation patterns.
RU: Статическая grep-проверка запрещённых паттернов raw SQL-интерполяции.
"""

from __future__ import annotations

from pathlib import Path
import re


_PATTERNS = [
    re.compile(r"text\(f"),
    re.compile(r"execute\(f"),
    re.compile(r"SELECT\s+.*\{.*\}"),
]


def main() -> None:
    """EN: Scan server files and fail on suspicious SQL string interpolation patterns.
    RU: Просканировать файлы server и завершиться ошибкой при подозрительных SQL-паттернах.
    """

    root = Path(__file__).resolve().parents[1]
    findings: list[str] = []

    for path in root.rglob("*.py"):
        if "/.venv" in str(path).replace("\\", "/"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            for pattern in _PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path}:{idx}:{line.strip()}")

    if findings:
        print("Forbidden SQL interpolation patterns found:")
        for item in findings:
            print(item)
        raise SystemExit(1)

    print("OK: no forbidden SQL interpolation patterns found.")


if __name__ == "__main__":
    main()
