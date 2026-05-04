# Backend

The backend starts with dependency-light Python modules so the assistant logic can
be tested immediately. The FastAPI entrypoint is included for the next phase.

## Verify Core Workflow

```powershell
python ../tests/smoke_test.py
```

## Run Local MVP Server

```powershell
python ../run_local_server.py
```

Then open `http://127.0.0.1:8000`.

## Future API Runtime

```powershell
pip install -r requirements.txt
uvicorn app.api:app --reload --port 8000
```
