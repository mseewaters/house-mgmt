"""
Daily Task Generation Service - Generate daily tasks from recurring task templates
Following Best-practices.md: Service layer business logic, UTC timestamps, structured logging
Following technical design: Daily task generation process
"""
from typing import List, Optional
from datetime import datetime, timezone, date
import re
from models.daily_task import DailyTaskCreate, DailyTaskModel
from dal.daily_task_dal import DailyTaskDAL
from dal.recurring_task_dal import RecurringTaskDAL
from utils.logging import log_info, log_error


class DailyTaskGenerationService:
    """
    Service for generating daily task instances from recurring task templates
    
    Responsibilities:
    - Query active recurring tasks
    - Apply frequency logic (Daily/Weekly/Monthly)
    - Generate daily task instances for specific dates
    - Prevent duplicate generation
    - Handle business validation
    """
    
    def __init__(self, table_name: str = None) -> None:
        """
        Initialize service with DAL dependencies
        
        Args:
            table_name: DynamoDB table name (optional, for testing)
        """
        self._daily_task_dal = DailyTaskDAL(table_name=table_name)
        self._recurring_task_dal = RecurringTaskDAL(table_name=table_name)
    
    def generate_daily_tasks_for_date(self, target_date: str) -> List[DailyTaskModel]:
        """
        Generate daily tasks for a specific date from active recurring tasks
        
        Args:
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            List of generated daily task instances
            
        Raises:
            ValueError: If date format is invalid or empty
            RuntimeError: If unexpected error occurs
        """
        try:
            # Validation (Best-practices.md: All inputs validated)
            if not target_date or not target_date.strip():
                raise ValueError("Date cannot be empty")
            
            # Validate date format
            target_date = target_date.strip()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', target_date):
                raise ValueError("Invalid date format. Expected YYYY-MM-DD")
            
            # Parse date to get day of week for weekly tasks
            try:
                parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                day_of_week = parsed_date.strftime('%A')  # Monday, Tuesday, etc.
                day_of_month = parsed_date.day
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYY-MM-DD")
            
            log_info(
                "Starting daily task generation",
                target_date=target_date,
                day_of_week=day_of_week,
                day_of_month=day_of_month
            )
            
            # Check if tasks already exist for this date (prevent duplicates)
            existing_tasks = self._daily_task_dal.get_daily_tasks_by_date(target_date)
            if existing_tasks:
                log_info(
                    "Daily tasks already exist for date, returning existing",
                    target_date=target_date,
                    existing_count=len(existing_tasks)
                )
                return existing_tasks
            
            # Get all active recurring tasks
            recurring_tasks = self._recurring_task_dal.get_all_recurring_tasks()
            active_tasks = [task for task in recurring_tasks if task.status == "Active"]
            
            log_info(
                "Retrieved recurring tasks for generation",
                total_recurring=len(recurring_tasks),
                active_tasks=len(active_tasks)
            )
            
            # Generate daily tasks based on frequency logic
            generated_tasks = []
            
            for recurring_task in active_tasks:
                should_generate = self._should_generate_task(
                    recurring_task, 
                    day_of_week, 
                    day_of_month
                )
                
                if should_generate:
                    daily_task_data = self._create_daily_task_from_recurring(
                        recurring_task, 
                        target_date
                    )
                    
                    # Create the daily task via DAL
                    created_task = self._daily_task_dal.create_daily_task(daily_task_data)
                    generated_tasks.append(created_task)
                    
                    log_info(
                        "Generated daily task from recurring template",
                        recurring_task_id=recurring_task.task_id,
                        daily_task_id=created_task.task_id,
                        task_name=created_task.task_name,
                        frequency=recurring_task.frequency
                    )
            
            log_info(
                "Daily task generation completed",
                target_date=target_date,
                generated_count=len(generated_tasks)
            )
            
            return generated_tasks
            
        except ValueError:
            # Re-raise validation errors (safe to return details)
            raise
        except Exception as e:
            # Log full details, return generic message (Best-practices.md requirement)
            log_error(
                "Failed to generate daily tasks",
                error=str(e),
                target_date=target_date if 'target_date' in locals() else None
            )
            raise RuntimeError("An error occurred while generating daily tasks")
    
    def _should_generate_task(self, recurring_task, day_of_week: str, day_of_month: int) -> bool:
        """
        Determine if a recurring task should generate a daily instance based on frequency
        
        Args:
            recurring_task: RecurringTaskModel instance
            day_of_week: Day name (Monday, Tuesday, etc.)
            day_of_month: Day of month (1-31)
            
        Returns:
            True if task should be generated for this date
        """
        frequency = recurring_task.frequency
        due = recurring_task.due
        
        if frequency == "Daily":
            # Daily tasks generate every day
            return True
        
        elif frequency == "Weekly":
            # Weekly tasks generate only on specified day (case-insensitive)
            return day_of_week.lower() == due.lower()
        
        elif frequency == "Monthly":
            # Monthly tasks generate only on specified day of month
            # Business rule: Monthly due dates must be 1-28 (valid for all months)
            try:
                target_day = int(due)
                if target_day < 1 or target_day > 28:
                    log_error(
                        "Monthly due day out of valid range (1-28)",
                        recurring_task_id=recurring_task.task_id,
                        due=due,
                        target_day=target_day
                    )
                    return False
                return day_of_month == target_day
            except (ValueError, TypeError):
                # Invalid monthly day format, skip this task
                log_error(
                    "Invalid monthly due day format for recurring task",
                    recurring_task_id=recurring_task.task_id,
                    due=due
                )
                return False
        
        else:
            # Unknown frequency, skip
            log_error(
                "Unknown frequency for recurring task",
                recurring_task_id=recurring_task.task_id,
                frequency=frequency
            )
            return False
    
    def _create_daily_task_from_recurring(self, recurring_task, target_date: str) -> DailyTaskCreate:
        """
        Create DailyTaskCreate instance from recurring task template
        
        Args:
            recurring_task: RecurringTaskModel template
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            DailyTaskCreate instance ready for DAL
        """
        # Map recurring task 'due' to daily task 'due_time'
        # Daily tasks: due = "Morning" or "Evening" -> use directly
        # Weekly tasks: due = "Sunday", "Monday", etc. -> default to "Morning"
        # Monthly tasks: due = "1", "15", etc. -> default to "Morning"
        
        if recurring_task.frequency == "Daily":
            # Daily tasks already have Morning/Evening
            due_time = recurring_task.due
        else:
            # Weekly and Monthly tasks default to Morning
            # TODO: In future, we could add time_of_day field to recurring tasks
            due_time = "Morning"
        
        return DailyTaskCreate(
            task_name=recurring_task.task_name,
            assigned_to=recurring_task.assigned_to,
            recurring_task_id=recurring_task.task_id,
            date=target_date,
            due_time=due_time,
            status="Pending",  # All generated tasks start as Pending
            category=recurring_task.category,
            overdue_when=recurring_task.overdue_when
        )