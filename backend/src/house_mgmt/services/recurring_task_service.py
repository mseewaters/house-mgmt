"""
Recurring Task Service Layer
Following Best-practices.md: API → Service → DAL separation
"""
from typing import List, Optional
from models.recurring_task import RecurringTaskCreate, RecurringTaskModel
from dal.recurring_task_dal import RecurringTaskDAL
from utils.logging import log_info, log_error


class RecurringTaskService:
    """
    Service layer for recurring task business logic
    
    Responsibilities:
    - Business rule validation
    - Coordinate between API and DAL layers
    - Handle service-level error scenarios
    - Logging business events
    """
    
    def __init__(self, dal: Optional[RecurringTaskDAL] = None) -> None:
        """
        Initialize service with DAL dependency injection
        
        Args:
            dal: Recurring task DAL instance (defaults to new instance)
        """
        self._dal = dal or RecurringTaskDAL()
    
    def create_recurring_task(self, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """
        Create a new recurring task with business validation
        
        Args:
            task_data: Validated recurring task creation data
            
        Returns:
            Created recurring task with generated ID and timestamps
            
        Raises:
            ValueError: For business rule violations
            RuntimeError: For unexpected persistence errors
        """
        try:
            log_info(
                "recurring_task_service_create_started",
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                frequency=task_data.frequency
            )
            
            # Business rule: Could add additional validations here
            # For example: Check that assigned_to family member exists, task limit checks, etc.
            
            # Delegate to DAL
            result = self._dal.create_recurring_task(task_data)
            
            log_info(
                "recurring_task_service_create_completed",
                task_id=result.task_id,
                task_name=result.task_name
            )
            
            return result
            
        except ValueError as e:
            # Re-raise validation errors from DAL
            log_error(
                "recurring_task_service_create_validation_error",
                error=str(e),
                task_name=task_data.task_name
            )
            raise
            
        except Exception as e:
            # Handle and log unexpected errors
            log_error(
                "recurring_task_service_create_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                task_name=task_data.task_name
            )
            raise RuntimeError("Failed to create recurring task") from e
    
    def get_recurring_task_by_id(self, task_id: str) -> Optional[RecurringTaskModel]:
        """
        Retrieve recurring task by ID
        
        Args:
            task_id: Unique recurring task identifier
            
        Returns:
            Recurring task if found, None otherwise (caller handles 404)
            
        Raises:
            RuntimeError: For unexpected persistence errors only
        """
        try:
            log_info(
                "recurring_task_service_get_by_id_started",
                task_id=task_id
            )
            
            # Delegate to DAL - let it return None for not found
            result = self._dal.get_recurring_task_by_id(task_id)
            
            if result:
                log_info(
                    "recurring_task_service_get_by_id_found",
                    task_id=task_id,
                    task_name=result.task_name
                )
            else:
                log_info(
                    "recurring_task_service_get_by_id_not_found",
                    task_id=task_id
                )
            
            # Return None - let the API layer handle 404 response
            return result
            
        except Exception as e:
            # Handle and log unexpected errors only
            log_error(
                "recurring_task_service_get_by_id_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                task_id=task_id
            )
            raise RuntimeError("Failed to retrieve recurring task") from e
    
    def get_all_recurring_tasks(self) -> List[RecurringTaskModel]:
        """
        Retrieve all recurring tasks
        
        Returns:
            List of all recurring tasks (empty list if none exist)
            
        Raises:
            RuntimeError: For unexpected persistence errors
        """
        try:
            log_info("recurring_task_service_get_all_started")
            
            # Delegate to DAL
            results = self._dal.get_all_recurring_tasks()
            
            log_info(
                "recurring_task_service_get_all_completed",
                count=len(results)
            )
            
            return results
            
        except Exception as e:
            # Handle and log unexpected errors
            log_error(
                "recurring_task_service_get_all_unexpected_error",
                error=str(e),
                error_type=type(e).__name__
            )
            raise RuntimeError("Failed to retrieve recurring tasks") from e
        
    def update_recurring_task(self, task_id: str, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """
        Update an existing recurring task
        
        Args:
            task_id: UUID of the recurring task to update
            task_data: Validated recurring task update data
            
        Returns:
            Updated recurring task with new timestamps
            
        Raises:
            ValueError: If recurring task not found
            Exception: For database errors
        """
        try:
            log_info(
                "recurring_task_service_update_started",
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                frequency=task_data.frequency
            )
            
            # Check if task exists first
            try:
                existing_task = self._dal.get_recurring_task_by_id(task_id)
            except ValueError:
                log_error(
                    "recurring_task_service_update_not_found",
                    task_id=task_id
                )
                raise ValueError(f"Recurring task not found: {task_id}")
            
            # Update via DAL
            updated_task = self._dal.update_recurring_task(task_id, task_data)
            
            log_info(
                "recurring_task_service_update_success",
                task_id=updated_task.task_id,
                task_name=updated_task.task_name,
                updated_at=updated_task.updated_at.isoformat()
            )
            
            return updated_task
            
        except ValueError:
            # Re-raise validation errors (task not found)
            raise
        except Exception as e:
            log_error(
                "recurring_task_service_update_error",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise


    def delete_recurring_task(self, task_id: str) -> None:
        """
        Delete a recurring task
        
        Args:
            task_id: UUID of the recurring task to delete
            
        Raises:
            ValueError: If recurring task not found
            Exception: For database errors
        """
        try:
            log_info(
                "recurring_task_service_delete_started",
                task_id=task_id
            )
            
            # Check if task exists first
            existing_task = self._dal.get_recurring_task_by_id(task_id)
            if existing_task is None:
                log_error("recurring_task_service_delete_not_found", task_id=task_id)
                raise ValueError(f"Recurring task not found: {task_id}")
            
            # Delete via DAL
            self._dal.delete_recurring_task(task_id)
            
            log_info(
                "recurring_task_service_delete_success",
                task_id=task_id,
                task_name=existing_task.task_name
            )
            
            # Note: For MVP, we're not cleaning up associated daily task instances
            # This preserves audit trail and completion history
            # Future enhancement could add cascade deletion or archiving
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            log_error(
                "recurring_task_service_delete_error",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
