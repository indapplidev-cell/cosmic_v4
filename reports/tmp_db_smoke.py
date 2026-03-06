from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        try:
            from server.config import DATABASE_URL as cfg_url
            db_url = cfg_url
        except Exception as exc:
            print(f"ERROR: failed to resolve DATABASE_URL: {exc}")
            return 1

    print(f"DATABASE_URL={db_url}")
    try:
        engine = create_engine(db_url, pool_pre_ping=True, future=True)
        with engine.connect() as conn:
            one = conn.execute(text("SELECT 1")).scalar_one()
            print(f"SELECT 1 -> {one}")
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print("Tables:")
            if not tables:
                print("  (no tables)")
            for name in tables:
                print(f"  - {name}")
    except Exception as exc:
        print(f"ERROR: DB smoke failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
