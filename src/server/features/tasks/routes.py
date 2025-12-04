"""Background tasks API endpoints"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
from pydantic import BaseModel
from ...celery_app import celery_app
from ...tasks import (
    analyze_demo_task,
    analyze_player_task,
    send_email_task
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["background-tasks"])


class TaskSubmitRequest(BaseModel):
    """Task submission request"""
    task_type: str
    params: Dict


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    result: Optional[Dict] = None
    error: Optional[str] = None


@router.post("/submit", response_model=Dict)
async def submit_task(request: TaskSubmitRequest):
    """
    Submit background task

    Task types:
    - analyze_demo
    - analyze_player
    - send_email
    """
    try:
        task_type = request.task_type
        params = request.params

        if task_type == "analyze_demo":
            task = analyze_demo_task.delay(
                params.get("demo_path"),
                params.get("user_id"),
            )
        elif task_type == "analyze_player":
            task = analyze_player_task.delay(
                params.get("player_nickname"),
            )
        elif task_type == "send_email":
            task = send_email_task.delay(
                params.get("to_email"),
                params.get("subject"),
                params.get("body"),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type: {task_type}",
            )

        return {
            "task_id": task.id,
            "status": "submitted",
            "task_type": task_type,
        }

    except HTTPException:
        # Preserve explicit HTTP errors (e.g. for unknown task types)
        raise
    except Exception as e:
        logger.exception(f"Task submission failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit task",
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get task status by ID"""
    try:
        result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": result.status,
        }

        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)

        return TaskStatusResponse(**response)

    except Exception as e:
        logger.exception(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get task status"
        )


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancel running task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)

        return {
            "task_id": task_id,
            "status": "cancelled"
        }

    except Exception as e:
        logger.exception(f"Failed to cancel task: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel task"
        )


@router.get("/stats")
async def get_worker_stats():
    """Get Celery worker statistics"""
    try:
        inspect = celery_app.control.inspect()

        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()

        return {
            "workers": stats,
            "active_tasks": active,
            "scheduled_tasks": scheduled,
            "reserved_tasks": reserved
        }

    except Exception as e:
        logger.exception(f"Failed to get worker stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get worker stats"
        )
