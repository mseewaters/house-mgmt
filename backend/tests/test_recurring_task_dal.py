"""
TDD: Recurring Task DAL Tests - Complete Coverage
Following TDD: Red → Green → Refactor
"""
import pytest
from datetime import datetime, timezone, date

def test_create_recurring_task_success():
    """Test creating a recurring task successfully"""
    from dal.recurring_task_dal import RecurringTaskDAL
    
    # Arrange - Create a simple task data object
    class TaskData:
        def __init__(self):
            self.task_name = "Morning pills"
            self.assigned_to = "member-uuid-123"
            self.frequency = "Daily"
            self.due = "Morning"
            self.overdue_when = "1 hour"
            self.category = "Medication"
            self.status = "Active"
    
    dal = RecurringTaskDAL()
    task_data = TaskData()
    
    # Act
    result = dal.create_recurring_task(task_data)
    
    # Assert
    assert result['task_id'] is not None
    assert result['task_name'] == "Morning pills"
    assert result['assigned_to'] == "member-uuid-123"
    assert result['frequency'] == "Daily"
    assert result['due'] == "Morning"
    assert result['overdue_when'] == "1 hour"
    assert result['category'] == "Medication"
    assert result['status'] == "Active"
    assert result['created_at'].tzinfo == timezone.utc
    assert result['updated_at'].tzinfo == timezone.utc


def test_generate_daily_tasks_from_recurring():
    """Test generating daily tasks from active recurring tasks"""
    from services.daily_task_service import DailyTaskService
    
    # Arrange
    service = DailyTaskService()
    target_date = date.today()
    
    # Act
    daily_tasks = service.generate_daily_tasks_for_date(target_date)
    
    # Assert - for now, just check it returns a list
    assert isinstance(daily_tasks, list)
    # More specific assertions will come once we implement the service


def test_complete_daily_task():
    """Test completing a daily task and updating status"""
    from services.daily_task_service import DailyTaskService
    
    # Arrange
    service = DailyTaskService()
    task_id = "task-123"
    completed_by = "member-456"
    
    # Act
    result = service.complete_task(task_id, completed_by)
    
    # Assert
    assert result is not None
    assert result['task_id'] == task_id
    assert result['status'] == "Completed"
    assert result['completed_by'] == completed_by
    assert result['completed_at'] is not None
    assert isinstance(result['completed_at'], datetime)
    assert result['completed_at'].tzinfo == timezone.utc


# NON-HAPPY PATH TESTS

def test_create_recurring_task_empty_name():
    """Test validation error when task name is empty"""
    from dal.recurring_task_dal import RecurringTaskDAL
    
    class InvalidTaskData:
        def __init__(self):
            self.task_name = ""  # Empty name
            self.assigned_to = "member-uuid-123"
            self.frequency = "Daily"
            self.due = "Morning"
            self.overdue_when = "1 hour"
            self.category = "Medication"
            self.status = "Active"
    
    dal = RecurringTaskDAL()
    task_data = InvalidTaskData()
    
    # Act & Assert
    with pytest.raises(ValueError, match="Task name cannot be empty"):
        dal.create_recurring_task(task_data)


def test_create_recurring_task_name_too_long():
    """Test validation error when task name exceeds 30 characters"""
    from dal.recurring_task_dal import RecurringTaskDAL
    
    class InvalidTaskData:
        def __init__(self):
            self.task_name = "This task name is definitely too long for our validation rules"  # >30 chars
            self.assigned_to = "member-uuid-123"
            self.frequency = "Daily"
            self.due = "Morning"
            self.overdue_when = "1 hour"
            self.category = "Medication"
            self.status = "Active"
    
    dal = RecurringTaskDAL()
    task_data = InvalidTaskData()
    
    # Act & Assert
    with pytest.raises(ValueError, match="Task name must be 30 characters or less"):
        dal.create_recurring_task(task_data)


def test_create_recurring_task_missing_assigned_to():
    """Test validation error when assigned_to is missing"""
    from dal.recurring_task_dal import RecurringTaskDAL
    
    class InvalidTaskData:
        def __init__(self):
            self.task_name = "Morning pills"
            self.assigned_to = ""  # Empty assigned_to
            self.frequency = "Daily"
            self.due = "Morning"
            self.overdue_when = "1 hour"
            self.category = "Medication"
            self.status = "Active"
    
    dal = RecurringTaskDAL()
    task_data = InvalidTaskData()
    
    # Act & Assert
    with pytest.raises(ValueError, match="assigned_to cannot be empty"):
        dal.create_recurring_task(task_data)


def test_complete_task_empty_task_id():
    """Test error when trying to complete task with empty ID"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    
    # Act & Assert
    with pytest.raises(ValueError, match="task_id cannot be empty"):
        service.complete_task("", "member-456")


def test_complete_task_empty_completed_by():
    """Test error when trying to complete task without completed_by"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    
    # Act & Assert
    with pytest.raises(ValueError, match="completed_by cannot be empty"):
        service.complete_task("task-123", "")


def test_complete_task_already_completed():
    """Test completing a task that's already completed"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    task_id = "task-123"
    
    # Arrange - Complete task first time
    first_completion = service.complete_task(task_id, "member-456")
    
    # Act - Try to complete again
    second_completion = service.complete_task(task_id, "member-789")
    
    # Assert - Should allow re-completion but update completed_by
    assert second_completion['completed_by'] == "member-789"
    assert second_completion['completed_at'] > first_completion['completed_at']


def test_generate_daily_tasks_invalid_date():
    """Test generating daily tasks with invalid date"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    
    # Act & Assert
    with pytest.raises(TypeError):
        service.generate_daily_tasks_for_date("invalid-date")  # Should be date object


def test_generate_daily_tasks_none_date():
    """Test generating daily tasks with None date"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    
    # Act & Assert
    with pytest.raises(ValueError, match="target_date cannot be None"):
        service.generate_daily_tasks_for_date(None)