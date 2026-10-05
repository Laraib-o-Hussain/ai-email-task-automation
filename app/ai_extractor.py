"""Pull structured task fields out of a free-text message."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

import httpx

from app.config import settings
from app.schemas import ExtractedTask, Priority


class AIExtractor:
    def extract(self, message: str) -> ExtractedTask:
        mode = settings.ai_mode.lower().strip()
        if mode == "mock":
            return self._mock_extract(message)
        if mode == "openai":
            return self._openai_extract(message)
        raise ValueError(f"Unknown AI_MODE={settings.ai_mode!r}. Use mock or openai.")

    def _mock_extract(self, message: str) -> ExtractedTask:
        # good enough for demos/tests — not a real NLP model
        text = " ".join(message.strip().split())
        lower = text.lower()

        assignee = "Unassigned"
        name_match = re.search(
            r"(?:remind|ask|tell|assign(?:ed)? to)\s+([A-Z][a-z]+)",
            text,
        )
        if name_match:
            assignee = name_match.group(1)
        else:
            any_name = re.search(r"\b([A-Z][a-z]{2,})\b", text)
            if any_name and any_name.group(1).lower() not in {"please", "friday", "monday"}:
                assignee = any_name.group(1)

        task = text
        for prefix in [
            r"^please\s+remind\s+\w+\s+to\s+",
            r"^please\s+ask\s+\w+\s+to\s+",
            r"^please\s+",
            r"^remind\s+\w+\s+to\s+",
            r"^ask\s+\w+\s+to\s+",
        ]:
            task = re.sub(prefix, "", task, flags=re.IGNORECASE)

        task = re.sub(r"\s+by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday).*$", "", task, flags=re.I)
        task = re.sub(r"\s+by\s+\d{4}-\d{2}-\d{2}.*$", "", task, flags=re.I)
        task = task.strip(" .")
        if task:
            task = task[0].upper() + task[1:]
        else:
            task = "Follow up on request"

        due_date = None
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        for name, target in weekdays.items():
            if name in lower:
                due_date = self._next_weekday(target).strftime("%Y-%m-%d")
                break

        iso_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        if iso_date:
            due_date = iso_date.group(1)

        due_time = None
        ampm = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lower)
        if ampm:
            hour = int(ampm.group(1))
            minute = int(ampm.group(2) or 0)
            period = ampm.group(3)
            if period == "pm" and hour != 12:
                hour += 12
            if period == "am" and hour == 12:
                hour = 0
            due_time = f"{hour:02d}:{minute:02d}"
        else:
            hhmm = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
            if hhmm:
                due_time = f"{int(hhmm.group(1)):02d}:{hhmm.group(2)}"

        priority = Priority.medium
        if "urgent" in lower or "asap" in lower or "high priority" in lower:
            priority = Priority.high
        elif "low priority" in lower or "whenever" in lower:
            priority = Priority.low

        return ExtractedTask(
            task=task[:255],
            assignee=assignee[:120],
            due_date=due_date,
            due_time=due_time,
            priority=priority,
        )

    def _openai_extract(self, message: str) -> ExtractedTask:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AI_MODE=openai")

        prompt = {
            "model": settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract a task from the user message. "
                        "Reply with JSON only using keys: "
                        "task, assignee, due_date (YYYY-MM-DD or null), "
                        "due_time (HH:MM or null), priority (low|medium|high)."
                    ),
                },
                {"role": "user", "content": message},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=prompt,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        data = json.loads(content)
        return ExtractedTask.model_validate(data)

    @staticmethod
    def _next_weekday(target: int):
        today = datetime.now().date()
        days_ahead = (target - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)


extractor = AIExtractor()
