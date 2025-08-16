"""
TDD: Task Status Update Lambda Tests - Automated status transitions
Following TDD: Red → Green → Refactor
Following Best-practices.md: Lambda handlers, scheduled processing, UTC timestamps
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from moto import mock_aws
import boto3
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch


@mock_aws
def test_task_status_lambda_updates_pending_to_overdue():
    """Test Lambda updates pending tasks to overdue when overdue_at time passed - WILL FAIL until Lambda exists"""
    # Arrange - Create daily tasks that should become overdue
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-status-test'
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
    
    # Create overdue task (overdue_at is 2 hours ago)
    now = datetime.now(timezone.utc)
    two_hours_ago = now - timedelta(hours=2)
    tomorrow = now + timedelta(days=1)
    future_time = now + timedelta(hours=6)  # 6 hours in the future
    
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    daily_dal = DailyTaskDAL(table_name=table_name)
    
    # Task that should become overdue
    overdue_task_data = DailyTaskCreate(
        task_name="Overdue morning pills",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Morning",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    
    # Create task and manually set overdue_at to past time
    created_task = daily_dal.create_daily_task(overdue_task_data)
    
    # Update overdue_at to past time (simulate task that should be overdue)
    table.update_item(
        Key={'PK': f'DAILY#{created_task.date}', 'SK': f'TASK#{created_task.task_id}'},
        UpdateExpression='SET overdue_at = :overdue_at, clear_at = :clear_at',
        ExpressionAttributeValues={
            ':overdue_at': two_hours_ago.isoformat(),
            ':clear_at': (now + timedelta(days=1)).isoformat()  # Clear tomorrow, not in 2024
        }
    )
    
    # Also create a task that should NOT become overdue (overdue_at is in future)
    future_task_data = DailyTaskCreate(
        task_name="Future task",
        assigned_to="member-uuid-123", 
        recurring_task_id="recurring-uuid-789",
        date="2024-08-02",
        due_time="Evening",
        status="Pending",
        category="Other",
        overdue_when="6 hours"
    )
    future_task = daily_dal.create_daily_task(future_task_data)

    # ALSO update the future task to have a proper future overdue_at
    table.update_item(
        Key={'PK': f'DAILY#{future_task.date}', 'SK': f'TASK#{future_task.task_id}'},
        UpdateExpression='SET overdue_at = :overdue_at',
        ExpressionAttributeValues={':overdue_at': future_time.isoformat()}
    )
    
    # Mock Lambda event and context
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = type('Context', (), {'aws_request_id': 'test-status-update'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_status_handler import lambda_handler
    
    # Act
    response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['pending_to_overdue'] == 1  # One task became overdue
    assert body['overdue_to_cleared'] >= 0   # May or may not have cleared tasks
    
    # Verify the overdue task status was updated
    updated_overdue_task = daily_dal.get_daily_task_by_id(created_task.task_id)
    assert updated_overdue_task.status == "Overdue"
    
    # Verify the future task is still pending
    updated_future_task = daily_dal.get_daily_task_by_id(future_task.task_id)
    assert updated_future_task.status == "Pending"


@mock_aws
def test_task_status_lambda_updates_overdue_to_cleared():
    """Test Lambda updates overdue tasks to cleared when clear_at time passed - WILL FAIL until Lambda exists"""
    # Arrange - Create overdue task that should be cleared
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-clear-test'
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
    
    now = datetime.now(timezone.utc)
    two_hours_ago = now - timedelta(hours=2)
    
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    daily_dal = DailyTaskDAL(table_name=table_name)
    
    # Create overdue task that should be cleared
    clear_task_data = DailyTaskCreate(
        task_name="Task to clear",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Morning",
        status="Overdue",  # Already overdue
        category="Medication",
        overdue_when="1 hour"
    )
    
    created_task = daily_dal.create_daily_task(clear_task_data)
    
    # Manually set status to Overdue and clear_at to past time
    table.update_item(
        Key={'PK': f'DAILY#{created_task.date}', 'SK': f'TASK#{created_task.task_id}'},
        UpdateExpression='SET #status = :status, clear_at = :clear_at',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'Overdue',
            ':clear_at': two_hours_ago.isoformat()
        }
    )
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = type('Context', (), {'aws_request_id': 'test-clear-update'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_status_handler import lambda_handler
    
    # Act
    response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['overdue_to_cleared'] == 1  # One task was cleared
    
    # Verify task was cleared
    updated_task = daily_dal.get_daily_task_by_id(created_task.task_id)
    assert updated_task.status == "Cleared"


@mock_aws
def test_task_status_lambda_handles_no_tasks_to_update():
    """Test Lambda handles case with no tasks needing status updates - WILL FAIL until Lambda exists"""
    # Arrange - Empty database
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-empty-status'
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
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = type('Context', (), {'aws_request_id': 'test-no-updates'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_status_handler import lambda_handler
    
    # Act
    response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['pending_to_overdue'] == 0
    assert body['overdue_to_cleared'] == 0
    assert 'No tasks required status updates' in body['message']


@mock_aws
def test_task_status_lambda_skips_completed_tasks():
    """Test Lambda doesn't modify completed tasks - WILL FAIL until Lambda exists"""
    # Arrange - Create completed task that's past overdue time
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-completed-test'
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
    
    now = datetime.now(timezone.utc)
    two_hours_ago = now - timedelta(hours=2)
    
    from dal.daily_task_dal import DailyTaskDAL
    from models.daily_task import DailyTaskCreate
    
    daily_dal = DailyTaskDAL(table_name=table_name)
    
    # Create completed task
    completed_task_data = DailyTaskCreate(
        task_name="Already completed task",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Morning",
        status="Completed",  # Already completed
        category="Medication",
        overdue_when="1 hour"
    )
    
    created_task = daily_dal.create_daily_task(completed_task_data)
    
    # Update to completed status and set overdue_at to past (should be ignored)
    table.update_item(
        Key={'PK': f'DAILY#{created_task.date}', 'SK': f'TASK#{created_task.task_id}'},
        UpdateExpression='SET #status = :status, overdue_at = :overdue_at, completed_at = :completed_at',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'Completed',
            ':overdue_at': two_hours_ago.isoformat(),
            ':completed_at': now.isoformat()
        }
    )
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = type('Context', (), {'aws_request_id': 'test-skip-completed'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_status_handler import lambda_handler
    
    # Act
    response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['pending_to_overdue'] == 0  # Completed task not changed
    
    # Verify task is still completed (unchanged)
    updated_task = daily_dal.get_daily_task_by_id(created_task.task_id)
    assert updated_task.status == "Completed"


def test_task_status_lambda_handles_database_error():
    """Test Lambda handles database errors gracefully - WILL FAIL until Lambda exists"""
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = type('Context', (), {'aws_request_id': 'test-db-error'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = 'non-existent-table'
    
    from lambdas.task_status_handler import lambda_handler
    
    # Mock service to raise exception
    with patch('lambdas.task_status_handler.DailyTaskDAL') as mock_dal_class:
        mock_dal_class.side_effect = Exception("DynamoDB connection failed")
        
        # Act
        response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['success'] is False
    assert 'An error occurred during task status updates' in body['error']


@mock_aws
def test_task_status_lambda_logs_execution_details():
    """Test Lambda logs execution metrics and details - WILL FAIL until Lambda exists"""
    # Arrange - Basic setup
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-status-logging'
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
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = type('Context', (), {'aws_request_id': 'test-status-logging'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_status_handler import lambda_handler
    
    # Act & Assert
    with patch('lambdas.task_status_handler.log_info') as mock_log_info:
        response = lambda_handler(event, context)
        
        # Verify logging occurred
        assert mock_log_info.called, "log_info should have been called"
        
        # Check for key log messages
        log_calls = [call[0][0] for call in mock_log_info.call_args_list]
        assert any('task_status_lambda_started' in call for call in log_calls)
        assert any('task_status_lambda_completed' in call for call in log_calls)
        
        # Verify successful response
        assert response['statusCode'] == 200