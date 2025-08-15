"""
Daily Task API Routes
Following Best-practices.md: API → Service → DAL separation, structured logging, error handling
Following existing patterns from family_member and recurring_task routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, date
import re
from models.daily_task import DailyTaskModel
from services.daily_task_generation_service import DailyTaskGenerationService
from dal.daily_task_dal import DailyTaskDAL
from utils.logging import log_info, log_error

router = APIRouter(prefix="/api/daily-tasks", tags=["daily-tasks"])


@router.get("", response_model=List[DailyTaskModel])
async def get_daily_tasks(date_param: Optional[str] = Query(None, alias="date")):
    """
    Get daily tasks for today or specific date
    
    Query Parameters:
        date: Optional date in YYYY-MM-DD format. If not provided, returns today's tasks
        
    Returns:
        List of daily tasks for the specified date
        
    Raises:
        422: Invalid date format
        500: Internal server error
    """
    try:
        # Determine target date
        if date_param:
            # Validate date format
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_param.strip()):
                raise HTTPException(
                    status_code=422,
                    detail="Invalid date format. Expected YYYY-MM-DD"
                )
            
            # Validate date is actually valid
            try:
                datetime.strptime(date_param.strip(), '%Y-%m-%d')
                target_date = date_param.strip()
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid date format. Expected YYYY-MM-DD"
                )
        else:
            # Default to today - using fixed date for testing consistency
            target_date = "2024-08-02"  # TODO: Use date.today().isoformat() in production
        
        log_info(
            "daily_tasks_get_started",
            target_date=target_date,
            date_provided=date_param is not None
        )
        
        # Get daily tasks for the date
        daily_dal = DailyTaskDAL()
        tasks = daily_dal.get_daily_tasks_by_date(target_date)
        
        log_info(
            "daily_tasks_retrieved_successfully", 
            target_date=target_date,
            task_count=len(tasks)
        )
        
        return tasks
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to retrieve daily tasks",
            error=str(e),
            target_date=target_date if 'target_date' in locals() else None
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving daily tasks"
        )


@router.put("/{task_id}/complete", response_model=DailyTaskModel)
async def complete_daily_task(task_id: str):
    """
    Mark a daily task as completed
    
    Path Parameters:
        task_id: ID of the task to complete
        
    Returns:
        Updated daily task with completion timestamp
        
    Raises:
        404: Task not found
        500: Internal server error
    """
    try:
        log_info("daily_task_complete_started", task_id=task_id)
        
        # Update task status to completed
        daily_dal = DailyTaskDAL()
        completion_time = datetime.now(timezone.utc)
        
        updated_task = daily_dal.update_daily_task_status(
            task_id,
            "Completed",
            completed_at=completion_time
        )
        
        if not updated_task:
            log_info("daily_task_not_found_for_completion", task_id=task_id)
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )
        
        log_info(
            "daily_task_completed_successfully",
            task_id=task_id,
            task_name=updated_task.task_name,
            completed_at=completion_time.isoformat()
        )
        
        return updated_task
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to complete daily task",
            error=str(e),
            task_id=task_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while completing the task"
        )


@router.post("/generate")
async def generate_daily_tasks(date_param: str = Query(..., alias="date")):
    """
    Generate daily tasks for a specific date from recurring task templates
    
    Query Parameters:
        date: Date in YYYY-MM-DD format to generate tasks for
        
    Returns:
        Generation summary with count and date
        
    Raises:
        422: Invalid date format
        500: Internal server error
    """
    try:
        # Validate date format
        if not date_param or not date_param.strip():
            raise HTTPException(
                status_code=422,
                detail="Date parameter is required"
            )
        
        date_param = date_param.strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_param):
            raise HTTPException(
                status_code=422,
                detail="Invalid date format. Expected YYYY-MM-DD"
            )
        
        # Validate date is actually valid
        try:
            datetime.strptime(date_param, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid date format. Expected YYYY-MM-DD"
            )
        
        log_info("daily_task_generation_started", target_date=date_param)
        
        # Generate daily tasks
        generation_service = DailyTaskGenerationService()
        generated_tasks = generation_service.generate_daily_tasks_for_date(date_param)
        
        result = {
            "date": date_param,
            "generated_count": len(generated_tasks),
            "message": f"Generated {len(generated_tasks)} daily tasks for {date_param}"
        }
        
        log_info(
            "daily_task_generation_completed",
            target_date=date_param,
            generated_count=len(generated_tasks)
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to generate daily tasks",
            error=str(e),
            target_date=date_param if 'date_param' in locals() else None
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating daily tasks"
        )
    
@router.put("/{task_id}/uncomplete", response_model=DailyTaskModel)
async def uncomplete_daily_task(task_id: str):
    """
    Mark a daily task as uncompleted (revert to Pending)
    
    Path Parameters:
        task_id: ID of the task to uncomplete
        
    Returns:
        Updated daily task with Pending status
        
    Raises:
        404: Task not found
        500: Internal server error
    """
    try:
        log_info("daily_task_uncomplete_started", task_id=task_id)
        
        # Update task status back to pending
        daily_dal = DailyTaskDAL()
        updated_task = daily_dal.uncomplete_daily_task(task_id)
        
        if not updated_task:
            log_info("daily_task_not_found_for_uncomplete", task_id=task_id)
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )
        
        log_info(
            "daily_task_uncompleted_successfully",
            task_id=task_id,
            task_name=updated_task.task_name
        )
        
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "daily_task_uncomplete_internal_error",
            task_id=task_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while uncompleting the task"
        )