"""
Recurring Task Data Access Layer with validation
Following Best-practices.md: Type hints, docstrings, structured logging
"""
from datetime import datetime, timezone
from typing import Dict, Any
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
        self._stored_tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_recurring_task(self, task_data: Any) -> Dict[str, Any]:
        """
        Create recurring task with validation and structured logging
        
        Args:
            task_data: Task creation data object
            
        Returns:
            Dict containing created task data with UTC timestamps
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validation (following Best-practices.md: All inputs validated)
            if not task_data.task_name or not task_data.task_name.strip():
                raise ValueError("Task name cannot be empty")
            
            if len(task_data.task_name.strip()) > 30:
                raise ValueError("Task name must be 30 characters or less")
            
            if not task_data.assigned_to or not task_data.assigned_to.strip():
                raise ValueError("assigned_to cannot be empty")
            
            # Generate UTC timestamps (Best-practices.md requirement)
            import uuid
            now = datetime.now(timezone.utc)
            task_id = str(uuid.uuid4())
            
            # Create task
            result = {
                'task_id': task_id,
                'task_name': task_data.task_name.strip(),
                'assigned_to': task_data.assigned_to,
                'frequency': task_data.frequency,
                'due': task_data.due,
                'overdue_when': task_data.overdue_when,
                'category': task_data.category,
                'status': task_data.status,
                'created_at': now,
                'updated_at': now
            }
            
            # Store in memory
            self._stored_tasks[task_id] = result
            
            # Structured logging (Best-practices.md requirement)
            log_info(
                "Recurring task created successfully",
                task_id=task_id,
                task_name=task_data.task_name.strip(),
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
                task_name=getattr(task_data, 'task_name', 'unknown')
            )
            raise RuntimeError("An error occurred while creating the recurring task")