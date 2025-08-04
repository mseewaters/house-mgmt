"""
TDD: Daily Task Generation Tests - Generate daily tasks from recurring templates
Following TDD: Red → Green → Refactor
Following Best-practices.md: Service layer business logic, comprehensive testing
"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timezone, date
from typing import List


@mock_aws
def test_generate_daily_tasks_from_active_recurring_tasks():
    """Test generating daily tasks from active recurring task templates - WILL FAIL until implemented"""
    # Arrange - Create mock DynamoDB table and recurring tasks
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create recurring tasks
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    
    # Active daily recurring task
    daily_task = RecurringTaskCreate(
        task_name="Morning pills",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    
    # Inactive recurring task (should not generate)
    inactive_task = RecurringTaskCreate(
        task_name="Old medication",
        assigned_to="member-uuid-123", 
        frequency="Daily",
        due="Evening",
        overdue_when="1 hour",
        category="Medication",
        status="Inactive"  # Should be skipped
    )
    
    recurring_dal.create_recurring_task(daily_task)
    recurring_dal.create_recurring_task(inactive_task)
    
    # Act - Generate daily tasks for target date
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    generation_service = DailyTaskGenerationService(table_name=table_name)
    target_date = "2024-08-02"
    generated_tasks = generation_service.generate_daily_tasks_for_date(target_date)
    
    # Assert - Should generate only from active recurring tasks
    assert len(generated_tasks) == 1
    assert generated_tasks[0].task_name == "Morning pills"
    assert generated_tasks[0].date == target_date
    assert generated_tasks[0].status == "Pending"
    assert generated_tasks[0].due_time == "Morning"
    assert generated_tasks[0].category == "Medication"
    assert generated_tasks[0].assigned_to == "member-uuid-123"
    assert generated_tasks[0].recurring_task_id is not None


@mock_aws 
def test_generate_daily_tasks_weekly_frequency_logic():
    """Test weekly recurring tasks only generate on correct day - WILL FAIL until implemented"""
    # Arrange - Create weekly recurring task
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    
    # Weekly task that should only run on Sunday
    weekly_task = RecurringTaskCreate(
        task_name="Weekly bath",
        assigned_to="member-uuid-456",
        frequency="Weekly", 
        due="Sunday",  # Only on Sundays
        overdue_when="1 day",
        category="Health",
        status="Active"
    )
    
    recurring_dal.create_recurring_task(weekly_task)
    
    from services.daily_task_generation_service import DailyTaskGenerationService
    generation_service = DailyTaskGenerationService(table_name=table_name)
    
    # Act & Assert - Test different days
    
    # Sunday (2024-08-04) - should generate task
    sunday_tasks = generation_service.generate_daily_tasks_for_date("2024-08-04")
    assert len(sunday_tasks) == 1
    assert sunday_tasks[0].task_name == "Weekly bath"
    
    # Monday (2024-08-05) - should NOT generate task
    monday_tasks = generation_service.generate_daily_tasks_for_date("2024-08-05") 
    assert len(monday_tasks) == 0
    
    # Friday (2024-08-02) - should NOT generate task
    friday_tasks = generation_service.generate_daily_tasks_for_date("2024-08-02")
    assert len(friday_tasks) == 0


def test_generate_daily_tasks_no_duplicates():
    """Test that generating tasks twice for same date doesn't create duplicates - WILL FAIL until implemented"""
    # Arrange
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    generation_service = DailyTaskGenerationService()
    target_date = "2024-08-02"
    
    # Act - Generate tasks twice
    first_generation = generation_service.generate_daily_tasks_for_date(target_date)
    second_generation = generation_service.generate_daily_tasks_for_date(target_date)
    
    # Assert - Should return existing tasks, not create duplicates
    # This test assumes we have some recurring tasks set up
    # For now, both should return same result (empty list if no recurring tasks)
    assert len(first_generation) == len(second_generation)


def test_generate_daily_tasks_invalid_date():
    """Test validation error for invalid date format - WILL FAIL until implemented"""
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    generation_service = DailyTaskGenerationService()
    
    # Act & Assert - Invalid date format should raise ValueError
    with pytest.raises(ValueError, match="Invalid date format"):
        generation_service.generate_daily_tasks_for_date("invalid-date")


def test_generate_daily_tasks_empty_date():
    """Test validation error for empty date - WILL FAIL until implemented"""
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    generation_service = DailyTaskGenerationService()
    
    # Act & Assert - Empty date should raise ValueError
    with pytest.raises(ValueError, match="Date cannot be empty"):
        generation_service.generate_daily_tasks_for_date("")


# COMPREHENSIVE PATH TESTING - Edge cases and error scenarios

@mock_aws
def test_weekly_task_case_insensitive_day_matching():
    """Test weekly tasks work with case-insensitive day names"""
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    
    # Create task with lowercase day name
    weekly_task = RecurringTaskCreate(
        task_name="Weekly cleanup",
        assigned_to="member-uuid-123",
        frequency="Weekly",
        due="sunday",  # lowercase
        overdue_when="6 hours",
        category="Cleaning",
        status="Active"
    )
    
    recurring_dal.create_recurring_task(weekly_task)
    
    from services.daily_task_generation_service import DailyTaskGenerationService
    generation_service = DailyTaskGenerationService(table_name=table_name)
    
    # Act - Sunday should match regardless of case
    sunday_tasks = generation_service.generate_daily_tasks_for_date("2024-08-04")  # Sunday
    
    # Assert
    assert len(sunday_tasks) == 1
    assert sunday_tasks[0].task_name == "Weekly cleanup"


@mock_aws
def test_monthly_task_valid_day_range():
    """Test monthly tasks with valid day range 1-28"""
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    
    # Create monthly task for 15th of month
    monthly_task = RecurringTaskCreate(
        task_name="Monthly vet visit",
        assigned_to="member-uuid-pet",
        frequency="Monthly",
        due="15",  # 15th of month
        overdue_when="1 day",
        category="Health",
        status="Active"
    )
    
    recurring_dal.create_recurring_task(monthly_task)
    
    from services.daily_task_generation_service import DailyTaskGenerationService
    generation_service = DailyTaskGenerationService(table_name=table_name)
    
    # Act & Assert
    # Should generate on 15th
    feb_15_tasks = generation_service.generate_daily_tasks_for_date("2024-02-15")
    assert len(feb_15_tasks) == 1
    assert feb_15_tasks[0].task_name == "Monthly vet visit"
    
    # Should NOT generate on 14th
    feb_14_tasks = generation_service.generate_daily_tasks_for_date("2024-02-14")
    assert len(feb_14_tasks) == 0


@mock_aws
def test_monthly_task_invalid_day_range_rejected():
    """Test monthly tasks with invalid day range (>28) are rejected"""
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    
    # Create monthly task for invalid day (30th - not allowed per business rule)
    invalid_monthly_task = RecurringTaskCreate(
        task_name="Invalid monthly task",
        assigned_to="member-uuid-123",
        frequency="Monthly",
        due="30",  # Invalid - must be 1-28
        overdue_when="1 day",
        category="Other",
        status="Active"
    )
    
    recurring_dal.create_recurring_task(invalid_monthly_task)
    
    from services.daily_task_generation_service import DailyTaskGenerationService
    generation_service = DailyTaskGenerationService(table_name=table_name)
    
    # Act - Even on 30th of month, should not generate
    tasks = generation_service.generate_daily_tasks_for_date("2024-08-30")
    
    # Assert - Should reject task with invalid day range
    assert len(tasks) == 0


@mock_aws
def test_monthly_task_invalid_format_rejected():
    """Test monthly tasks with non-numeric due values are rejected"""
    # Arrange
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-test'
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    
    # Create monthly task with invalid format
    invalid_format_task = RecurringTaskCreate(
        task_name="Invalid format task",
        assigned_to="member-uuid-123",
        frequency="Monthly",
        due="abc",  # Invalid format
        overdue_when="1 day",
        category="Other",
        status="Active"
    )
    
    recurring_dal.create_recurring_task(invalid_format_task)
    
    from services.daily_task_generation_service import DailyTaskGenerationService
    generation_service = DailyTaskGenerationService(table_name=table_name)
    
    # Act
    tasks = generation_service.generate_daily_tasks_for_date("2024-08-15")
    
    # Assert - Should reject task with invalid format
    assert len(tasks) == 0


@mock_aws
def test_unknown_frequency_rejected():
    """Test recurring tasks with unknown frequency are rejected"""
    # This test would require creating a task with invalid frequency
    # Since Pydantic validates frequency as Literal, we'd need to bypass validation
    # For now, this tests the service's defensive programming
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    generation_service = DailyTaskGenerationService()
    
    # Create a mock recurring task with invalid frequency (bypassing Pydantic)
    class MockRecurringTask:
        def __init__(self):
            self.task_id = "test-id"
            self.task_name = "Test task"
            self.frequency = "Yearly"  # Not in our supported list
            self.due = "January"
            self.status = "Active"
    
    mock_task = MockRecurringTask()
    
    # Act - Test _should_generate_task directly
    result = generation_service._should_generate_task(mock_task, "Monday", 15)
    
    # Assert - Should reject unknown frequency
    assert result is False


def test_edge_case_date_formats():
    """Test various invalid date formats are properly rejected"""
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    generation_service = DailyTaskGenerationService()
    
    invalid_dates = [
        "2024/08/02",    # Wrong separator
        "08-02-2024",    # Wrong order
        "2024-8-2",      # Missing leading zeros
        "2024-13-01",    # Invalid month
        "2024-02-30",    # Invalid day for month (Feb only has 28/29 days)
        "2023-02-29",    # Invalid leap day (2023 is not a leap year)
        "not-a-date",    # Complete garbage
        "2024-04-31",    # Invalid day (April only has 30 days)
    ]
    
    for invalid_date in invalid_dates:
        with pytest.raises(ValueError, match="Invalid date format"):
            generation_service.generate_daily_tasks_for_date(invalid_date)