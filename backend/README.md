# Backend

Run the FastAPI scaffold from the repo root with:

```bash
uvicorn app.main:app --app-dir backend --reload
```

The scaffold defaults to mock `llm`, `search`, and `cache` adapters unless real provider settings are configured in `backend/.env`.
