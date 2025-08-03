"""
Recurring Task Data Access Layer with validation
Clean implementation using Pydantic models throughout
Following Best-practices.md: Type hints, docstrings, structured logging
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict
from models.recurring_task import RecurringTaskCreate, RecurringTaskModel
from utils.logging import log_info, log_error


class RecurringTaskDAL:
    """DAL for recurring task operations with validation"""
    
    def __init__(self, table_name: str = None) -> None:
        """
        Initialize DAL with optional table name
        
        Args:
            table_name: DynamoDB table name. If None, uses default
        """
        self.table_name = table_name or 'house-mgmt-dev'
        self._stored_tasks: Dict[str, RecurringTaskModel] = {}
    
    def create_recurring_task(self, task_data: RecurringTaskCreate) -> RecurringTaskModel:
        """
        Create recurring task with validation and structured logging
        
        Args:
            task_data: Validated Pydantic recurring task creation data
            
        Returns:
            RecurringTaskModel with generated ID and timestamps
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If unexpected error occurs
        """
        try:
            # Generate UTC timestamps (Best-practices.md requirement)
            import uuid
            now = datetime.now(timezone.utc)
            task_id = str(uuid.uuid4())
            
            # Create Pydantic model directly
            result = RecurringTaskModel(
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                frequency=task_data.frequency,
                due=task_data.due,
                overdue_when=task_data.overdue_when,
                category=task_data.category,
                status=task_data.status,
                created_at=now,
                updated_at=now
            )
            
            # Store in memory
            self._stored_tasks[task_id] = result
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Recurring task created successfully",
                task_id=task_id,
                task_name=task_data.task_name,
                assigned_to=task_data.assigned_to,
                frequency=task_data.frequency
            )
            
            return result
            
        except ValueError:
            # Re-raise validation errors (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to create recurring task",
                error=str(e),
                task_name=task_data.task_name
            )
            raise RuntimeError("An error occurred while creating the recurring task")
    
    def get_recurring_task_by_id(self, task_id: str) -> Optional[RecurringTaskModel]:
        """
        Retrieve recurring task by ID with structured logging
        
        Args:
            task_id: Unique recurring task identifier
            
        Returns:
            RecurringTaskModel if found, None otherwise
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            result = self._stored_tasks.get(task_id)
            
            if result:
                log_info("Recurring task retrieved successfully", task_id=task_id)
            else:
                log_info("Recurring task not found", task_id=task_id)
            
            return result
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve recurring task",
                error=str(e),
                task_id=task_id
            )
            raise RuntimeError("An error occurred while retrieving the recurring task")
    
    def get_all_recurring_tasks(self) -> List[RecurringTaskModel]:
        """
        Retrieve all recurring tasks with structured logging
        
        Returns:
            List of all recurring tasks (empty list if none exist)
            
        Raises:
            RuntimeError: If unexpected error occurs
        """
        try:
            results = list(self._stored_tasks.values())
            
            log_info(
                "All recurring tasks retrieved successfully",
                count=len(results)
            )
            
            return results
            
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to retrieve all recurring tasks",
                error=str(e)
            )
            raise RuntimeError("An error occurred while retrieving recurring tasks")