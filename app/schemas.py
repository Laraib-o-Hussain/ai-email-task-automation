from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ExtractRequest(BaseModel):
    message: str = Field(min_length=3, max_length=4000)


class ExtractedTask(BaseModel):
    task: str = Field(min_length=1, max_length=255)
    assignee: str = Field(min_length=1, max_length=120)
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: Priority = Priority.medium

    @field_validator("due_date")
    @classmethod
    def validate_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("due_date must be YYYY-MM-DD") from exc
        return value

    @field_validator("due_time")
    @classmethod
    def validate_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("due_time must be HH:MM") from exc
        return value


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    assignee: str = Field(min_length=1, max_length=120)
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: Priority = Priority.medium
    source_message: Optional[str] = None

    @field_validator("due_date")
    @classmethod
    def validate_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("due_date must be YYYY-MM-DD") from exc
        return value

    @field_validator("due_time")
    @classmethod
    def validate_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("due_time must be HH:MM") from exc
        return value


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    assignee: Optional[str] = Field(default=None, min_length=1, max_length=120)
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: Optional[Priority] = None

    @field_validator("due_date")
    @classmethod
    def validate_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("due_date must be YYYY-MM-DD") from exc
        return value

    @field_validator("due_time")
    @classmethod
    def validate_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("due_time must be HH:MM") from exc
        return value


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    assignee: str
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    priority: str
    source_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
