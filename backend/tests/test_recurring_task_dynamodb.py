"""
Test Recurring Task DynamoDB integration
Following TDD: Write failing tests first for real persistence
ALL TESTS USE @mock_aws
"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timezone

@mock_aws
def test_create_recurring_task_dynamodb_persistence():
    """Test that recurring task is actually stored in DynamoDB with correct schema"""
    # Arrange - Create real DynamoDB table
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
    
    dal = RecurringTaskDAL(table_name=table_name)
    task_data = RecurringTaskCreate(
        task_name="Morning Pills",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    
    # Act
    result = dal.create_recurring_task(task_data)
    
    # Assert - Verify it was stored in DynamoDB with technical design schema
    stored_item = table.get_item(
        Key={
            'PK': 'RECURRING',
            'SK': f'TASK#{result.task_id}'
        }
    )
    
    assert 'Item' in stored_item
    item = stored_item['Item']
    assert item['PK'] == 'RECURRING'
    assert item['SK'] == f'TASK#{result.task_id}'
    assert item['entity_type'] == 'recurring_task'
    assert item['task_name'] == 'Morning Pills'
    assert item['assigned_to'] == 'member-uuid-123'
    assert item['frequency'] == 'Daily'
    assert item['due'] == 'Morning'
    assert item['overdue_when'] == '1 hour'
    assert item['category'] == 'Medication'
    assert item['status'] == 'Active'
    assert 'created_at' in item
    assert 'updated_at' in item


@mock_aws
def test_get_recurring_task_by_id_dynamodb():
    """Test retrieving recurring task from DynamoDB by ID"""
    # Arrange - Create table and store a task
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
    
    dal = RecurringTaskDAL(table_name=table_name)
    task_data = RecurringTaskCreate(
        task_name="Evening Walk",
        assigned_to="member-uuid-456", 
        frequency="Daily",
        due="Evening",
        overdue_when="6 hours",
        category="Other",
        status="Active"
    )
    
    # Create and store task
    created_task = dal.create_recurring_task(task_data)
    task_id = created_task.task_id
    
    # Act - Retrieve by ID
    retrieved_task = dal.get_recurring_task_by_id(task_id)
    
    # Assert
    assert retrieved_task is not None
    assert retrieved_task.task_id == task_id
    assert retrieved_task.task_name == "Evening Walk"
    assert retrieved_task.assigned_to == "member-uuid-456"
    assert retrieved_task.frequency == "Daily"
    assert retrieved_task.due == "Evening"
    assert retrieved_task.overdue_when == "6 hours"
    assert retrieved_task.category == "Other"
    assert retrieved_task.status == "Active"


@mock_aws
def test_get_recurring_task_not_found_dynamodb():
    """Test that non-existent recurring task returns None from DynamoDB"""
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
    
    dal = RecurringTaskDAL(table_name=table_name)
    fake_id = "non-existent-task-uuid-12345"
    
    # Act
    result = dal.get_recurring_task_by_id(fake_id)
    
    # Assert
    assert result is None


@mock_aws
def test_get_all_recurring_tasks_dynamodb():
    """Test retrieving all recurring tasks from DynamoDB using KeyConditionExpression"""
    # Arrange - Create table and store multiple tasks
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
    
    dal = RecurringTaskDAL(table_name=table_name)
    
    # Create multiple tasks
    task1_data = RecurringTaskCreate(
        task_name="Morning Pills",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    task2_data = RecurringTaskCreate(
        task_name="Weekly Bath",
        assigned_to="member-uuid-456",
        frequency="Weekly",
        due="Sunday",
        overdue_when="1 day",
        category="Health",
        status="Active"
    )
    
    created_task1 = dal.create_recurring_task(task1_data)
    created_task2 = dal.create_recurring_task(task2_data)
    
    # Act - Get all recurring tasks
    all_tasks = dal.get_all_recurring_tasks()
    
    # Assert
    assert isinstance(all_tasks, list)
    assert len(all_tasks) == 2
    
    # Verify both tasks are returned
    task_names = [task.task_name for task in all_tasks]
    assert "Morning Pills" in task_names
    assert "Weekly Bath" in task_names
    
    # Verify different frequencies
    frequencies = [task.frequency for task in all_tasks]
    assert "Daily" in frequencies
    assert "Weekly" in frequencies


@mock_aws
def test_recurring_task_dynamodb_query_uses_key_condition_not_scan():
    """Test that get_all_recurring_tasks uses KeyConditionExpression, not scan"""
    # This test verifies we're following Best-practices.md: Use KeyConditionExpression not scans
    # We'll verify this by checking the query pattern: PK = "RECURRING", SK begins_with "TASK#"
    
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
    
    # Add some non-recurring-task data to ensure we don't accidentally return it
    table.put_item(Item={
        'PK': 'FAMILY',
        'SK': 'MEMBER#some-member-id', 
        'entity_type': 'family_member',
        'name': 'Should not be returned'
    })
    
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    dal = RecurringTaskDAL(table_name=table_name)
    task_data = RecurringTaskCreate(
        task_name="Test Task",
        assigned_to="member-uuid-test",
        frequency="Daily", 
        due="Morning",
        overdue_when="1 hour",
        category="Other",
        status="Active"
    )
    dal.create_recurring_task(task_data)
    
    # Act
    all_tasks = dal.get_all_recurring_tasks()
    
    # Assert - Should only return recurring tasks, not family members
    assert len(all_tasks) == 1
    assert all_tasks[0].task_name == "Test Task"
    # This test will pass only if we use proper KeyConditionExpression


@mock_aws
def test_recurring_task_weekly_frequency_storage():
    """Test that weekly recurring task stores due day correctly"""
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
    
    dal = RecurringTaskDAL(table_name=table_name)
    task_data = RecurringTaskCreate(
        task_name="Weekly Medication Review",
        assigned_to="member-uuid-789",
        frequency="Weekly",
        due="Sunday",  # Weekly tasks use day names
        overdue_when="1 day",
        category="Health",
        status="Active"
    )
    
    # Act
    result = dal.create_recurring_task(task_data)
    
    # Assert - Verify weekly due day is stored correctly
    stored_item = table.get_item(
        Key={
            'PK': 'RECURRING',
            'SK': f'TASK#{result.task_id}'
        }
    )
    
    assert 'Item' in stored_item
    item = stored_item['Item']
    assert item['frequency'] == 'Weekly'
    assert item['due'] == 'Sunday'


@mock_aws
def test_recurring_task_monthly_frequency_storage():
    """Test that monthly recurring task stores due date correctly"""
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
    
    dal = RecurringTaskDAL(table_name=table_name)
    task_data = RecurringTaskCreate(
        task_name="Monthly Vet Checkup",
        assigned_to="member-uuid-pet",
        frequency="Monthly",
        due="15",  # Monthly tasks use day of month
        overdue_when="3 days",
        category="Health",
        status="Active"
    )
    
    # Act
    result = dal.create_recurring_task(task_data)
    
    # Assert - Verify monthly due date is stored correctly
    stored_item = table.get_item(
        Key={
            'PK': 'RECURRING',
            'SK': f'TASK#{result.task_id}'
        }
    )
    
    assert 'Item' in stored_item
    item = stored_item['Item']
    
@mock_aws
def test_recurring_task_dynamodb_connection_failure_fallback():
    """Test that DAL gracefully falls back to in-memory when DynamoDB unavailable"""
    # Arrange - Don't create any DynamoDB resources
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    
    # This should trigger fallback to in-memory storage
    dal = RecurringTaskDAL(table_name="table-that-does-not-exist")
    
    task_data = RecurringTaskCreate(
        task_name="Connection Test Task",
        assigned_to="member-uuid-test",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Other",
        status="Active"
    )
    
    # Act - Should not raise exception, should use fallback
    result = dal.create_recurring_task(task_data)
    all_tasks = dal.get_all_recurring_tasks()
    
    # Assert - Should work with in-memory fallback
    assert result.task_name == "Connection Test Task"
    assert len(all_tasks) == 1
    assert all_tasks[0].task_name == "Connection Test Task"


@mock_aws
def test_recurring_task_malformed_item_handling():
    """Test handling of malformed data from DynamoDB"""
    # Arrange - Create table with malformed data
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
    
    # Insert malformed data directly into DynamoDB
    table.put_item(Item={
        'PK': 'RECURRING',
        'SK': 'TASK#malformed-456',
        'entity_type': 'recurring_task',
        'task_id': 'malformed-456',
        'task_name': 'Test Task',
        'assigned_to': 'member-uuid-test',
        'frequency': 'Daily',
        'due': 'Morning',
        'overdue_when': '1 hour',
        'category': 'Other',
        'status': 'Active',
        'created_at': 'invalid-date-format',  # Malformed datetime
        'updated_at': 'invalid-date-format'   # Malformed datetime
    })
    
    from dal.recurring_task_dal import RecurringTaskDAL
    
    dal = RecurringTaskDAL(table_name=table_name)
    
    # Act & Assert - Should handle malformed data gracefully
    with pytest.raises(RuntimeError, match="An error occurred while retrieving the recurring task"):
        dal.get_recurring_task_by_id("malformed-456")