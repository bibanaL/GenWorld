# GenWorld Backend

Local development commands should use `py` on this machine.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
```

The default SQLite database path is `data/genworld.db`.

## Test

```powershell
.\.venv\Scripts\python -m unittest discover -s backend\tests -v
```

The tests use a temporary SQLite database through `GENWORLD_DATABASE_PATH`.
