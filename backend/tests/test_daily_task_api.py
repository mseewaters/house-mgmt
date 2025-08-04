"""
TDD: Daily Task API Tests - REST endpoints for daily task operations
Following TDD: Red → Green → Refactor  
Following existing API patterns from family_member and recurring_task APIs
"""
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
import boto3


@mock_aws
def test_get_daily_tasks_for_today_success():
    """Test GET /api/daily-tasks returns today's tasks - WILL FAIL until endpoint exists"""
    # Arrange - Create mock DynamoDB and some tasks
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
    
    # Create recurring task and generate daily tasks
    from dal.recurring_task_dal import RecurringTaskDAL
    from models.recurring_task import RecurringTaskCreate
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    recurring_task = RecurringTaskCreate(
        task_name="Morning pills",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Morning",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    recurring_dal.create_recurring_task(recurring_task)
    
    # Generate daily tasks for today
    generation_service = DailyTaskGenerationService(table_name=table_name)
    today_date = "2024-08-02"  # Fixed date for testing
    generation_service.generate_daily_tasks_for_date(today_date)
    
    # Set up FastAPI client with test table
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from main import app
    client = TestClient(app)
    
    # Act - GET daily tasks for today
    response = client.get("/api/daily-tasks")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_name"] == "Morning pills"
    assert data[0]["status"] == "Pending"
    assert data[0]["due_time"] == "Morning"
    assert data[0]["category"] == "Medication"


@mock_aws
def test_get_daily_tasks_for_specific_date():
    """Test GET /api/daily-tasks?date=YYYY-MM-DD returns tasks for specific date - WILL FAIL until implemented"""
    # Arrange - Similar setup as above
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
    from services.daily_task_generation_service import DailyTaskGenerationService
    
    recurring_dal = RecurringTaskDAL(table_name=table_name)
    recurring_task = RecurringTaskCreate(
        task_name="Evening pills",
        assigned_to="member-uuid-123",
        frequency="Daily",
        due="Evening",
        overdue_when="1 hour",
        category="Medication",
        status="Active"
    )
    recurring_dal.create_recurring_task(recurring_task)
    
    # Generate tasks for specific date
    generation_service = DailyTaskGenerationService(table_name=table_name)
    target_date = "2024-08-03"
    generation_service.generate_daily_tasks_for_date(target_date)
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from main import app
    client = TestClient(app)
    
    # Act - GET tasks for specific date
    response = client.get(f"/api/daily-tasks?date={target_date}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_name"] == "Evening pills"
    assert data[0]["date"] == target_date


def test_get_daily_tasks_invalid_date_format():
    """Test GET /api/daily-tasks?date=invalid returns 422 validation error - WILL FAIL until implemented"""
    from main import app
    client = TestClient(app)
    
    # Act - Request with invalid date format
    response = client.get("/api/daily-tasks?date=invalid-date")
    
    # Assert
    assert response.status_code == 422
    assert "Invalid date format" in response.text


@mock_aws
def test_complete_daily_task_success():
    """Test PUT /api/daily-tasks/{id}/complete marks task as completed - WILL FAIL until implemented"""
    # Arrange - Create daily task
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
    
    daily_dal = DailyTaskDAL(table_name=table_name)
    task_data = DailyTaskCreate(
        task_name="Test task",
        assigned_to="member-uuid-123",
        recurring_task_id="recurring-uuid-456",
        date="2024-08-02",
        due_time="Morning",
        status="Pending",
        category="Medication",
        overdue_when="1 hour"
    )
    created_task = daily_dal.create_daily_task(task_data)
    
    import os
    os.environ['DYNAMODB_TABLE'] = table_name
    
    from main import app
    client = TestClient(app)
    
    # Act - Complete the task
    response = client.put(f"/api/daily-tasks/{created_task.task_id}/complete")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Completed"
    assert data["completed_at"] is not None
    assert data["task_id"] == created_task.task_id


def test_complete_daily_task_not_found():
    """Test PUT /api/daily-tasks/{id}/complete returns 404 for non-existent task - WILL FAIL until implemented"""
    from main import app
    client = TestClient(app)
    
    # Act - Try to complete non-existent task
    response = client.put("/api/daily-tasks/non-existent-id/complete")
    
    # Assert
    assert response.status_code == 404
    assert "not found" in response.text.lower()


def test_generate_daily_tasks_endpoint():
    """Test POST /api/daily-tasks/generate?date=YYYY-MM-DD generates tasks for date - WILL FAIL until implemented"""
    from main import app
    client = TestClient(app)
    
    target_date = "2024-08-02"
    
    # Act - Generate tasks for specific date
    response = client.post(f"/api/daily-tasks/generate?date={target_date}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "generated_count" in data
    assert "date" in data
    assert data["date"] == target_date


def test_generate_daily_tasks_invalid_date():
    """Test POST /api/daily-tasks/generate?date=invalid returns 422 - WILL FAIL until implemented"""
    from main import app
    client = TestClient(app)
    
    # Act - Generate with invalid date
    response = client.post("/api/daily-tasks/generate?date=invalid-date")
    
    # Assert
    assert response.status_code == 422
    assert "Invalid date format" in response.text