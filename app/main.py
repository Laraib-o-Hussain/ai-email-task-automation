from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.ai_extractor import extractor
from app.config import settings
from app.database import Base, engine, get_db
from app.models import Task
from app.schemas import (
    ExtractRequest,
    ExtractedTask,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

app = FastAPI(title=settings.app_name, version="0.1.0")
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "ai_mode": settings.ai_mode}


@app.post("/extract-task", response_model=ExtractedTask)
def extract_task(payload: ExtractRequest):
    try:
        return extractor.extract(payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # network / API issues
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc


@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    row = Task(
        title=payload.title,
        assignee=payload.assignee,
        due_date=payload.due_date,
        due_time=payload.due_time,
        priority=payload.priority.value,
        source_message=payload.source_message,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.id.desc()).all()


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    row = db.get(Task, task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    row = db.get(Task, task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    for key, value in data.items():
        setattr(row, key, value.value if hasattr(value, "value") else value)

    db.commit()
    db.refresh(row)
    return row


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    row = db.get(Task, task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(row)
    db.commit()
    return {"message": "Task deleted", "id": task_id}
