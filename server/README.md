# Server DB Module (SQLAlchemy + Alembic)

## 1) Create virtual environment and install deps

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Configure database URL

Default (SQLite):

```bash
export DATABASE_URL="sqlite:///./server/app.db"
```

PostgreSQL example:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/app_db"
```

## 3) Create migration (autogenerate)

```bash
alembic -c server/alembic.ini revision --autogenerate -m "init"
```

## 4) Apply migrations

```bash
alembic -c server/alembic.ini upgrade head
```

## 5) Optional smoke check

```bash
python -m server.scripts.smoke_auth
```
