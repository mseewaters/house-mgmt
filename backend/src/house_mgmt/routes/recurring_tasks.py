"""
Recurring Task API routes
Following Best-practices.md: API → Service → DAL architecture
"""
from typing import List
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from models.recurring_task import RecurringTaskCreate, RecurringTaskModel
from services.recurring_task_service import RecurringTaskService
from utils.logging import log_info, log_error

router = APIRouter(prefix="/api", tags=["recurring-tasks"])

# Initialize service
recurring_task_service = RecurringTaskService()


@router.post("/recurring-tasks", status_code=status.HTTP_201_CREATED)
async def create_recurring_task(
    request: Request,
    task_data: RecurringTaskCreate
) -> RecurringTaskModel:
    """
    Create a new recurring task
    
    Args:
        request: FastAPI request object (for correlation ID)
        task_data: Validated recurring task data
        
    Returns:
        Created recurring task with timestamps
        
    Raises:
        HTTPException: 422 for validation errors, 500 for internal errors
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "create_recurring_task_requested",
            task_name=task_data.task_name,
            assigned_to=task_data.assigned_to,
            frequency=task_data.frequency,
            correlation_id=correlation_id
        )
        
        # Create via service layer
        result = recurring_task_service.create_recurring_task(task_data)
        
        log_info(
            "create_recurring_task_success",
            task_id=result.task_id,
            task_name=result.task_name,
            correlation_id=correlation_id
        )
        
        return result
        
    except ValueError as e:
        # Business logic validation errors
        log_error(
            "create_recurring_task_validation_error",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
        
    except Exception as e:
        # Internal server errors
        log_error(
            "create_recurring_task_internal_error",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the recurring task"
        )


@router.get("/recurring-tasks/{task_id}")
async def get_recurring_task(
    request: Request,
    task_id: str
) -> RecurringTaskModel:
    """
    Get recurring task by ID
    
    Args:
        request: FastAPI request object (for correlation ID)
        task_id: Recurring task UUID
        
    Returns:
        Recurring task data
        
    Raises:
        HTTPException: 404 if not found, 500 for internal errors
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "get_recurring_task_requested",
            task_id=task_id,
            correlation_id=correlation_id
        )
        
        # Retrieve via service layer
        result = recurring_task_service.get_recurring_task_by_id(task_id)
        
        if result is None:
            log_info(
                "get_recurring_task_not_found",
                task_id=task_id,
                correlation_id=correlation_id
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Recurring task not found"}
            )
        
        log_info(
            "get_recurring_task_success",
            task_id=task_id,
            task_name=result.task_name,
            correlation_id=correlation_id
        )
        
        return result
        
    except Exception as e:
        # Internal server errors
        log_error(
            "get_recurring_task_internal_error",
            error=str(e),
            error_type=type(e).__name__,
            task_id=task_id,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the recurring task"
        )


@router.get("/recurring-tasks")
async def get_all_recurring_tasks(request: Request) -> List[RecurringTaskModel]:
    """
    Get all recurring tasks
    
    Args:
        request: FastAPI request object (for correlation ID)
        
    Returns:
        List of all recurring tasks
        
    Raises:
        HTTPException: 500 for internal errors
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "get_all_recurring_tasks_requested",
            correlation_id=correlation_id
        )
        
        # Retrieve via service layer
        results = recurring_task_service.get_all_recurring_tasks()
        
        log_info(
            "get_all_recurring_tasks_success",
            count=len(results),
            correlation_id=correlation_id
        )
        
        return results
        
    except Exception as e:
        # Internal server errors
        log_error(
            "get_all_recurring_tasks_internal_error",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving recurring tasks"
        )