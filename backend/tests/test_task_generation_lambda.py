"""
TDD: Task Generation Lambda Tests - Scheduled background task generation
Following TDD: Red → Green → Refactor
Following Best-practices.md: Lambda handlers, EventBridge events, structured logging
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from moto import mock_aws
import boto3
import json
from datetime import datetime, timezone, date, timedelta
from unittest.mock import patch


@mock_aws
def test_task_generation_lambda_handler_generates_tasks_for_tomorrow():
    """Test Lambda handler generates tasks for tomorrow - WILL FAIL until Lambda exists"""
    # Arrange - Create mock DynamoDB with recurring tasks
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
    
    # Daily task
    daily_task = RecurringTaskCreate(
        task_name="Morning medication",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    
    # Weekly task (only on Sundays)
    weekly_task = RecurringTaskCreate(
        task_name="Weekly bath",
        assigned_to="member-uuid-456",
        frequency="Weekly", 
        due="Sunday",
        overdue_when="6 hours",
        category="Health",
        status="Active"
    )
    
    recurring_dal.create_recurring_task(daily_task)
    recurring_dal.create_recurring_task(weekly_task)
    
    # Mock EventBridge event (scheduled trigger)
    event = {
        "source": ["aws.events"],
        "detail-type": ["Scheduled Event"],
        "detail": {}
    }
    context = type('Context', (), {'aws_request_id': 'test-request-id'})()
    
    # Set environment variables
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_generation_handler import lambda_handler
    
    # Act - Execute Lambda with tomorrow's date
    with patch('lambdas.task_generation_handler.get_tomorrow_date') as mock_tomorrow:
        # Mock tomorrow as Sunday so weekly task generates too
        mock_tomorrow.return_value = "2024-08-04"  # Sunday
        
        response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['generated_count'] >= 2  # Daily + Weekly task
    assert body['target_date'] == "2024-08-04"
    assert 'execution_time_ms' in body
    
    # Verify tasks were actually created in database
    from dal.daily_task_dal import DailyTaskDAL
    daily_dal = DailyTaskDAL(table_name=table_name)
    created_tasks = daily_dal.get_daily_tasks_by_date("2024-08-04")
    assert len(created_tasks) >= 2
    
    task_names = [task.task_name for task in created_tasks]
    assert "Morning medication" in task_names
    assert "Weekly bath" in task_names  # Sunday task


@mock_aws
def test_task_generation_lambda_handles_no_recurring_tasks():
    """Test Lambda gracefully handles no recurring tasks - WILL FAIL until implemented"""
    # Arrange - Empty DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-empty-test'
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
    
    event = {
        "source": ["aws.events"],
        "detail-type": ["Scheduled Event"],
        "detail": {}
    }
    context = type('Context', (), {'aws_request_id': 'test-request-id-empty'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_generation_handler import lambda_handler
    
    # Act
    response = lambda_handler(event, context)
    
    # Assert - Should succeed with 0 tasks generated
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['generated_count'] == 0
    assert 'No recurring tasks found' in body['message']


@mock_aws
def test_task_generation_lambda_prevents_duplicate_generation():
    """Test Lambda doesn't generate duplicate tasks if run multiple times - WILL FAIL until implemented"""
    # Arrange - Setup recurring task
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-duplicate-test'
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
    task_data = RecurringTaskCreate(
        task_name="Daily task",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Other",
        status="Active"
    )
    recurring_dal.create_recurring_task(task_data)
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"], "detail": {}}
    context = type('Context', (), {'aws_request_id': 'test-duplicate'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_generation_handler import lambda_handler
    
    # Act - Run Lambda twice for same date
    with patch('lambdas.task_generation_handler.get_tomorrow_date') as mock_tomorrow:
        mock_tomorrow.return_value = "2024-08-05"
        
        # First run - should generate task
        response1 = lambda_handler(event, context)
        body1 = json.loads(response1['body'])
        
        # Second run - should not duplicate
        response2 = lambda_handler(event, context)
        body2 = json.loads(response2['body'])
    
    # Assert
    assert response1['statusCode'] == 200
    assert response2['statusCode'] == 200
    assert body1['generated_count'] == 1  # First run generates
    assert body2['generated_count'] == 1  # Second run returns existing (no new generation)
    
    # Verify only one task exists in database
    from dal.daily_task_dal import DailyTaskDAL
    daily_dal = DailyTaskDAL(table_name=table_name)
    tasks = daily_dal.get_daily_tasks_by_date("2024-08-05")
    assert len(tasks) == 1  # No duplicates


def test_task_generation_lambda_handles_database_error():
    """Test Lambda handles database errors gracefully - WILL FAIL until implemented"""
    # Arrange - Invalid table configuration  
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"], "detail": {}}
    context = type('Context', (), {'aws_request_id': 'test-error'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = 'non-existent-table'
    
    from lambdas.task_generation_handler import lambda_handler
    
    # Mock the service to raise an exception (simulate database failure)
    with patch('lambdas.task_generation_handler.DailyTaskGenerationService') as mock_service_class:
        mock_service_class.side_effect = Exception("DynamoDB connection failed")
        
        # Act
        response = lambda_handler(event, context)
    
    # Assert - Should return error response, not crash
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['success'] is False
    assert 'error' in body
    assert 'An error occurred during task generation' in body['error']


def test_get_tomorrow_date_utility():
    """Test utility function for getting tomorrow's date - WILL FAIL until implemented"""
    from lambdas.task_generation_handler import get_tomorrow_date
    
    # Act
    tomorrow = get_tomorrow_date()
    
    # Assert - Should return tomorrow's date in YYYY-MM-DD format
    expected_tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert tomorrow == expected_tomorrow
    assert len(tomorrow) == 10  # YYYY-MM-DD format
    assert tomorrow.count('-') == 2


@mock_aws
def test_task_generation_lambda_logs_execution_details():
    """Test Lambda logs important execution details - WILL FAIL until implemented"""
    # Arrange - Setup basic test
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table_name = 'house-mgmt-logging-test'
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
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"], "detail": {}}
    context = type('Context', (), {'aws_request_id': 'test-logging'})()
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from lambdas.task_generation_handler import lambda_handler
    
    # Act & Assert - Should not crash and should include logging
    with patch('lambdas.task_generation_handler.log_info') as mock_log_info:
        response = lambda_handler(event, context)
        
        # Verify logging calls were made
        assert mock_log_info.called, "log_info should have been called"
        
        # Check for key log messages
        log_calls = [call[0][0] for call in mock_log_info.call_args_list]
        assert any('task_generation_lambda_started' in call for call in log_calls), f"Expected 'started' log, got: {log_calls}"
        assert any('task_generation_lambda_completed' in call for call in log_calls), f"Expected 'completed' log, got: {log_calls}"
        
        # Verify response is successful
        assert response['statusCode'] == 200