# Email Lookup Service (FastAPI)

Implements the PRD: look up a user's email by checking **HuggingFace → GitHub → Blog** (in that order).  
First valid email is **validated, normalized, cached (Redis)**, **stored (SQLite)**, and returned.

## Quick Start (Docker)
```bash
cd email-lookup-service
cp .env.example .env   # optional: edit values
docker compose up --build
```
Service runs at `http://localhost:8080`.

## Endpoints
- `POST /lookup` — Triggers the ordered lookup and returns the result (and persists it).
- `GET /emails/{key}` — Fetch a previously-stored record by its key.
- `GET /health` — Liveness probe.
- `GET /metrics` — Prometheus metrics (if enabled).

## Request shape
```json
POST /lookup
{
  "username": "john",
  "huggingface": "john",       // optional; defaults to "username"
  "github": "john",            // optional; defaults to "username"
  "blog_url": "https://blog.example.com",  // optional
  "force_refresh": false
}
```

## .env
See `.env.example`. Provide `REDIS_URL` to enable distributed rate limiting and caching.

## Local (no Docker)
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

## Notes
- Tokens for GitHub/HuggingFace are optional (raise rate limits).
- Blog discovery tries the given `blog_url` directly, and if it's a root page it also tries `/feed`, `/rss`, and parses content for emails.
- Rate limiting: default **60 req/min** per-IP using Redis if configured, otherwise in-memory fallback.
- Caching: positive results are cached for `CACHE_TTL_SECONDS` (12h by default).
