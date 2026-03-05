"""
EN: Run Buildozer with an explicit spec file path to avoid cwd/spec ambiguity.
RU: Запуск Buildozer с явным путем к spec-файлу, чтобы исключить неоднозначность cwd/spec.
"""

from __future__ import annotations

import sys
from pathlib import Path

from buildozer import Buildozer, BuildozerCommandException, BuildozerException


def main() -> int:
    """
    EN: Execute Buildozer commands using the project-local `_buildozer_cfg/buildozer.spec`.
    RU: Выполнить команды Buildozer, используя проектный `_buildozer_cfg/buildozer.spec`.
    """

    root_dir = Path(__file__).resolve().parents[1]
    spec_path = root_dir / "_buildozer_cfg" / "buildozer.spec"

    try:
        Buildozer(str(spec_path)).run_command(sys.argv[1:])
        return 0
    except BuildozerCommandException:
        return 1
    except BuildozerException as exc:
        Buildozer(str(spec_path)).error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
