# Cosmic v4 KivyMD Bootstrap

## Python Version
- EN: Python 3.11.x (confirmed installed and used for the venv).
- RU: Python 3.11.x (подтверждена установка и использована для venv).

## Requirements split
- EN: `requirements.txt` is for desktop (Windows) environment.
- RU: `requirements.txt` предназначен для desktop-среды (Windows).
- EN: `requirements_android.txt` contains Android runtime dependencies.
- RU: `requirements_android.txt` содержит runtime-зависимости для Android.

## Setup (Create venv)
### Windows
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
```

### macOS / Linux
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## Upgrade tooling
```bash
python -m pip install -U pip setuptools wheel
```

## Install dependencies
```bash
pip install kivy
pip install "kivymd @ git+https://github.com/kivymd/KivyMD.git@master"
```

## Generate requirements.txt (after install)
```bash
pip freeze > requirements.txt
```

## Run
```bash
python main.py
```

## Manual smoke test
- EN: Verify the app opens in landscape, the Login screen is visible, and clicking "Регистрация" switches to Register. Click "Уже есть аккаунт?" to return to Login.
- RU: Проверьте, что приложение открывается в ландшафтной ориентации, виден экран входа, и нажатие "Регистрация" переключает на регистрацию. Нажмите "Уже есть аккаунт?" чтобы вернуться к входу.

## Compatibility
- EN: Installed successfully on Windows with Python 3.11.x, Kivy 2.3.1 (cp311 wheel), and KivyMD master at commit d668d8b2b3d9eb54517892f613ffe34d9914517a. No workaround needed.
- RU: Установка успешно выполнена на Windows с Python 3.11.x, Kivy 2.3.1 (cp311 wheel) и KivyMD master на коммите d668d8b2b3d9eb54517892f613ffe34d9914517a. Обходные решения не требуются.
