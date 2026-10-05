# AI Email → Task Automation

Tiny demo that takes a sentence that looks like an email request, pulls out a task (assignee / due date / etc.), and stores it through a small FastAPI API.

There's a real AI hook via env vars, but by default it runs in **mock mode** so you can clone and run it without an API key.

## Flow

```
message text
    → FastAPI
    → AIExtractor (mock or real)
    → validated JSON
    → Task saved in SQLite
```

## Stack

- FastAPI / Pydantic
- SQLite
- Docker
- pytest

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # or cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

Docs: http://localhost:8001/docs

## Docker

```bash
docker compose up --build
```

## Endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | health |
| POST | `/extract-task` | NL → structured task (does not save) |
| POST | `/tasks` | create task |
| GET | `/tasks` | list |
| GET | `/tasks/{id}` | one task |
| PUT | `/tasks/{id}` | update |
| DELETE | `/tasks/{id}` | delete |

## Example

Request to `/extract-task`:

```json
{
  "message": "Please remind Sarah to prepare the monthly sales report by Friday at 3 PM."
}
```

Mock response looks like:

```json
{
  "task": "Prepare the monthly sales report",
  "assignee": "Sarah",
  "due_date": "2026-10-09",
  "due_time": "15:00",
  "priority": "medium"
}
```

## AI modes

In `.env`:

```
AI_MODE=mock
# AI_MODE=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
```

Mock mode is the default and what the tests use.

## Tests

```bash
pytest -v
```
