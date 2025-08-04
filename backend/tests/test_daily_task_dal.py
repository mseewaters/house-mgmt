"""
TDD: Daily Task DAL Tests - Following existing pattern from recurring_task_dal
Following TDD: Red → Green → Refactor
Following Best-practices.md: KeyConditionExpression queries, UTC timestamps, structured logging
ALL TESTS USE @mock_aws for isolated DynamoDB testing
"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timezone, date
from pydantic import ValidationError


def test_create_daily_task_success():
    """Test creating a daily task successfully - following recurring task pattern"""
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    # Arrange - Use real Pydantic model following existing pattern
    dal = DailyTaskDAL()
    task_data = DailyTaskCreate(
        task_name="Morning pills",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Morning",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    
    # Act
    result = dal.create_daily_task(task_data)
    
    # Assert - Use Pydantic model attributes, following existing pattern
    assert result.task_id is not None
    assert result.task_name == "Morning pills"
    assert result.assigned_to == "member-uuid-123"
    assert result.recurring_task_id == "recurring-uuid-456"
    assert result.date == "2024-08-02"
    assert result.due_time == "Morning"
    assert result.status == "Pending"
    assert result.category == "Medication"
    assert result.overdue_when == "1 hour"
    assert result.completed_at is None
    assert result.generated_at.tzinfo == timezone.utc
    assert result.overdue_at.tzinfo == timezone.utc
    assert result.clear_at.tzinfo == timezone.utc
    assert result.created_at.tzinfo == timezone.utc
    assert result.updated_at.tzinfo == timezone.utc


def test_get_daily_task_by_id_success():
    """Test retrieving daily task by ID - following existing pattern"""
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    # Arrange - Create a task first
    dal = DailyTaskDAL()
    task_data = DailyTaskCreate(
        task_name="Evening pills",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Evening",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    created_task = dal.create_daily_task(task_data)
    
    # Act
    retrieved_task = dal.get_daily_task_by_id(created_task.task_id)
    
    # Assert
    assert retrieved_task is not None
    assert retrieved_task.task_id == created_task.task_id
    assert retrieved_task.task_name == "Evening pills"
    assert retrieved_task.due_time == "Evening"


def test_get_daily_task_by_id_not_found():
    """Test retrieving non-existent daily task returns None - following existing pattern"""
    from dal.daily_task_dal import DailyTaskDAL
    
    # Arrange
    dal = DailyTaskDAL()
    
    # Act
    result = dal.get_daily_task_by_id("non-existent-id")
    
    # Assert
    assert result is None


@mock_aws
def test_get_daily_tasks_by_date():
    """Test querying daily tasks by date using KeyConditionExpression with mocked DynamoDB"""
    # Arrange - Create mock DynamoDB table (simplified like recurring task tests)
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
    
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    dal = DailyTaskDAL(table_name=table_name)
    target_date = "2024-08-02"
    
    task1_data = DailyTaskCreate(
        task_name="Morning pills",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date=target_date,
        due_time="Morning",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    
    task2_data = DailyTaskCreate(
        task_name="Evening pills",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-789",
        date=target_date,
        due_time="Evening",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    
    # Create task for different date (should not be returned)
    task3_data = DailyTaskCreate(
        task_name="Other day task",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-999",
        date="2024-08-03",  # Different date
        due_time="Morning",
        status="Pending",
        category="Other",
        overdue_when="1 hour"
    )
    
    dal.create_daily_task(task1_data)
    dal.create_daily_task(task2_data)
    dal.create_daily_task(task3_data)
    
    # Act - Query by date using technical design pattern: PK = "DAILY#2024-08-02"
    tasks = dal.get_daily_tasks_by_date(target_date)
    
    # Assert - Should only return tasks for specified date
    assert len(tasks) == 2
    task_names = [task.task_name for task in tasks]
    assert "Morning pills" in task_names
    assert "Evening pills" in task_names
    assert "Other day task" not in task_names


@mock_aws
def test_update_daily_task_status():
    """Test updating daily task status with completion timestamp using mocked DynamoDB"""
    # Arrange - Create mock DynamoDB table (simplified like recurring task tests)
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
    
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    dal = DailyTaskDAL(table_name=table_name)
    task_data = DailyTaskCreate(
        task_name="Morning pills",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Morning",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    created_task = dal.create_daily_task(task_data)
    
    # Act - Update status to completed
    completion_time = datetime.now(timezone.utc)
    updated_task = dal.update_daily_task_status(
        created_task.task_id,
        "Completed",
        completed_at=completion_time
    )
    
    # Assert
    assert updated_task.status == "Completed"
    assert updated_task.completed_at is not None
    assert updated_task.completed_at.tzinfo == timezone.utc
    assert updated_task.updated_at > created_task.updated_at


# NON-HAPPY PATH TESTS - Following existing pattern

def test_create_daily_task_empty_name():
    """Test validation error when task name is empty - using Pydantic validation"""
    from models.daily_task import DailyTaskCreate
    
    # Act & Assert - Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        DailyTaskCreate(
            task_name="",  # Empty name
            assigned_to="member-uuid-123",
            recurring_task_id="recurring-uuid-456",
            date="2024-08-02",
            due_time="Morning",
            status="Pending",
            category="Medication",
            overdue_when="1 hour"
        )
    
    assert "Task name cannot be empty" in str(exc_info.value)


def test_create_daily_task_invalid_status():
    """Test validation error for invalid status - using Pydantic validation"""
    from models.daily_task import DailyTaskCreate
    
    # Act & Assert - Only specific status values allowed
    with pytest.raises(ValidationError) as exc_info:
        DailyTaskCreate(
            task_name="Morning pills",
            assigned_to="member-uuid-123",
            recurring_task_id="recurring-uuid-456",
            date="2024-08-02",
            due_time="Morning",
            status="InvalidStatus",  # Invalid status
            category="Medication",
            overdue_when="1 hour"
        )
    
    assert "Input should be" in str(exc_info.value)


def test_create_daily_task_invalid_due_time():
    """Test validation error for invalid due_time - using Pydantic validation"""
    from models.daily_task import DailyTaskCreate
    
    # Act & Assert - Only Morning/Evening allowed
    with pytest.raises(ValidationError) as exc_info:
        DailyTaskCreate(
            task_name="Morning pills",
            assigned_to="member-uuid-123",
            recurring_task_id="recurring-uuid-456",
            date="2024-08-02",
            due_time="InvalidTime",  # Invalid due_time
            status="Pending",
            category="Medication",
            overdue_when="1 hour"
        )
    
    assert "Input should be" in str(exc_info.value)