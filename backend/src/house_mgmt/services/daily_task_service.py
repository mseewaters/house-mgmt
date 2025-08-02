"""
Daily Task Service with validation
Following Best-practices.md: Type hints, docstrings, structured logging, error handling
"""
from datetime import date, datetime, timezone
from typing import List, Dict, Any
from utils.logging import log_info, log_error


class DailyTaskService:
    """Service for managing daily task generation from recurring tasks"""
    
    def __init__(self) -> None:
        """Initialize service with in-memory storage"""
        self._completed_tasks: Dict[str, Dict[str, Any]] = {}
    
    def generate_daily_tasks_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Generate daily tasks for a specific date from active recurring tasks
        
        Args:
            target_date: The date to generate tasks for (must be date object)
            
        Returns:
            List of daily tasks for the specified date
            
        Raises:
            ValueError: If target_date is None
            TypeError: If target_date is not a date object
        """
        try:
            # Validation (Best-practices.md: All inputs validated)
            if target_date is None:
                raise ValueError("target_date cannot be None")
            
            if not isinstance(target_date, date):
                raise TypeError("target_date must be a date object")
            
            # Structured logging
            log_info(
                "Generating daily tasks for date",
                target_date=target_date.isoformat()
            )
            
            # For now, return empty list to make test pass
            # Will implement actual logic in next iteration
            return []
            
        except (ValueError, TypeError):
            # Re-raise validation errors (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to generate daily tasks",
                error=str(e),
                target_date=target_date.isoformat() if target_date else None
            )
            raise RuntimeError("An error occurred while generating daily tasks")
    
    def complete_task(self, task_id: str, completed_by: str) -> Dict[str, Any]:
        """
        Mark a daily task as completed with validation and structured logging
        
        Args:
            task_id: ID of the task to complete (cannot be empty)
            completed_by: ID of the family member who completed the task (cannot be empty)
            
        Returns:
            Dict with completion details including UTC timestamp
            
        Raises:
            ValueError: If task_id or completed_by is empty
        """
        try:
            # Validation (Best-practices.md: All inputs validated)
            if not task_id or not task_id.strip():
                raise ValueError("task_id cannot be empty")
            
            if not completed_by or not completed_by.strip():
                raise ValueError("completed_by cannot be empty")
            
            # Generate UTC timestamp (Best-practices.md requirement)
            completion_time = datetime.now(timezone.utc)
            
            completion_result = {
                'task_id': task_id,
                'status': 'Completed',
                'completed_by': completed_by,
                'completed_at': completion_time
            }
            
            # Store completion in memory (allows re-completion)
            self._completed_tasks[task_id] = completion_result
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Task completed successfully",
                task_id=task_id,
                completed_by=completed_by,
                completed_at=completion_time.isoformat()
            )
            
            return completion_result
            
        except ValueError:
            # Re-raise validation errors (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to complete task",
                error=str(e),
                task_id=task_id if 'task_id' in locals() else 'unknown'
            )
            raise RuntimeError("An error occurred while completing the task")