"""
TDD: Recurring Task DAL Tests - Updated for Pydantic Models
Following TDD: Red → Green → Refactor
"""
import pytest
from datetime import datetime, timezone, date
from pydantic import ValidationError

def test_create_recurring_task_success():
    """Test creating a recurring task successfully"""
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    # Arrange - Use real Pydantic model
    dal = RecurringTaskDAL()
    task_data = RecurringTaskCreate(
        task_name="Morning pills",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    
    # Act
    result = dal.create_recurring_task(task_data)
    
    # Assert - Use Pydantic model attributes, not dictionary access
    assert result.task_id is not None
    assert result.task_name == "Morning pills"
    assert result.assigned_to == "member-uuid-123"
    assert result.frequency == "Daily"
    assert result.due == "Morning"
    assert result.overdue_when == "1 hour"
    assert result.category == "Medication"
    assert result.status == "Active"
    assert result.created_at.tzinfo == timezone.utc
    assert result.updated_at.tzinfo == timezone.utc


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


# NON-HAPPY PATH TESTS - Now using Pydantic validation

def test_create_recurring_task_empty_name():
    """Test validation error when task name is empty"""
    from models.recurring_task import RecurringTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        RecurringTaskCreate(
            task_name="",  # Empty name
            assigned_to="member-uuid-123",
            frequency="Daily",
            due="Morning",
            overdue_when="1 hour",
            category="Medication",
            status="Active"
        )
    
    assert "Task name cannot be empty" in str(exc_info.value)


def test_create_recurring_task_name_too_long():
    """Test validation error when task name exceeds 30 characters"""
    from models.recurring_task import RecurringTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        RecurringTaskCreate(
            task_name="This task name is definitely too long for our validation rules",  # >30 chars
            assigned_to="member-uuid-123",
            frequency="Daily",
            due="Morning",
            overdue_when="1 hour",
            category="Medication",
            status="Active"
        )
    
    assert "30 characters" in str(exc_info.value)


def test_create_recurring_task_missing_assigned_to():
    """Test validation error when assigned_to is missing"""
    from models.recurring_task import RecurringTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        RecurringTaskCreate(
            task_name="Morning pills",
            assigned_to="",  # Empty assigned_to
            frequency="Daily",
            due="Morning",
            overdue_when="1 hour",
            category="Medication",
            status="Active"
        )
    
    assert "assigned_to cannot be empty" in str(exc_info.value)


def test_complete_task_empty_task_id():
    """Test error when trying to complete task with empty ID"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    
    # Act & Assert
    with pytest.raises(ValueError, match="task_id cannot be empty"):
        service.complete_task("", "member-456")


def test_complete_task_empty_completed_by():
    """Test error when trying to complete task with empty completed_by"""
    from services.daily_task_service import DailyTaskService
    
    service = DailyTaskService()
    
    # Act & Assert
    with pytest.raises(ValueError, match="completed_by cannot be empty"):
        service.complete_task("task-123", "")


def test_create_recurring_task_invalid_frequency():
    """Test validation error for invalid frequency"""
    from models.recurring_task import RecurringTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        RecurringTaskCreate(
            task_name="Test Task",
            assigned_to="member-uuid-123",
            frequency="Hourly",  # Invalid frequency
            due="Morning",
            overdue_when="1 hour",
            category="Medication",
            status="Active"
        )
    
    # Should mention valid options
    error_str = str(exc_info.value)
    assert "Daily" in error_str or "Weekly" in error_str or "Monthly" in error_str


def test_create_recurring_task_invalid_category():
    """Test validation error for invalid category"""
    from models.recurring_task import RecurringTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        RecurringTaskCreate(
            task_name="Test Task",
            assigned_to="member-uuid-123",
            frequency="Daily",
            due="Morning",
            overdue_when="1 hour",
            category="Shopping",  # Invalid category
            status="Active"
        )
    
    # Should mention valid options
    error_str = str(exc_info.value)
    assert any(cat in error_str for cat in ["Medication", "Feeding", "Health", "Cleaning", "Other"])


def test_create_recurring_task_invalid_overdue_when():
    """Test validation error for invalid overdue_when"""
    from models.recurring_task import RecurringTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        RecurringTaskCreate(
            task_name="Test Task",
            assigned_to="member-uuid-123",
            frequency="Daily",
            due="Morning",
            overdue_when="2 hours",  # Invalid overdue_when
            category="Medication",
            status="Active"
        )
    
    # Should mention valid options
    error_str = str(exc_info.value)
    assert any(opt in error_str for opt in ["Immediate", "1 hour", "6 hours", "1 day"])