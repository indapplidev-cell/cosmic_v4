import json
from pathlib import Path
from typing import Optional

from kivy.app import App


class UserSession:
    _FILENAME = "user_session.json"

    def _path(self) -> Path:
        app = App.get_running_app()
        base = Path(getattr(app, "user_data_dir", Path.cwd()))
        return base / self._FILENAME

    def set_email(self, email: str) -> None:
        email = (email or "").strip()
        if not email:
            return
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"email": email}, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_email(self) -> Optional[str]:
        path = self._path()
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
        except Exception:
            return None
        email = (data.get("email") or "").strip()
        return email or None

    def is_logged_in(self) -> bool:
        return self.get_email() is not None

    def clear(self) -> None:
        path = self._path()
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass
