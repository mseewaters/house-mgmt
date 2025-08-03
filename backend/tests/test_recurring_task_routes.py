"""
Test Recurring Task API routes
Following TDD: Write failing tests first
"""
import pytest
import json

# HAPPY PATH TESTS

def test_create_recurring_task_success(client):
    """Test successful creation of a recurring task"""
    # Arrange - First create a family member to assign task to
    person_data = {
        "name": "Sarah",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    task_data = {
        "task_name": "Morning Pills",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=task_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["task_name"] == "Morning Pills"
    assert data["assigned_to"] == member_id
    assert data["frequency"] == "Daily"
    assert data["due"] == "Morning"
    assert data["overdue_when"] == "1 hour"
    assert data["category"] == "Medication"
    assert data["status"] == "Active"
    assert "task_id" in data
    assert "created_at" in data
    assert "updated_at" in data
    # Verify correlation ID is in response headers
    assert "X-Correlation-ID" in response.headers


def test_get_recurring_task_success(client):
    """Test successful retrieval of recurring task by ID"""
    # Arrange - First create a family member and task
    person_data = {"name": "John", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    task_data = {
        "task_name": "Evening Walk",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Evening",
        "overdue_when": "6 hours",
        "category": "Other",
        "status": "Active"
    }
    create_response = client.post("/api/recurring-tasks", json=task_data)
    created_task = create_response.json()
    task_id = created_task["task_id"]
    
    # Act
    response = client.get(f"/api/recurring-tasks/{task_id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["task_name"] == "Evening Walk"
    assert data["assigned_to"] == member_id
    assert "X-Correlation-ID" in response.headers


def test_get_all_recurring_tasks_success(client):
    """Test successful retrieval of all recurring tasks"""
    # Arrange - Create a family member and couple tasks
    person_data = {"name": "Alice", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    task1_data = {
        "task_name": "Morning Pills",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    task2_data = {
        "task_name": "Weekly Bath",
        "assigned_to": member_id,
        "frequency": "Weekly",
        "due": "Sunday",
        "overdue_when": "1 day",
        "category": "Health",
        "status": "Active"
    }
    
    client.post("/api/recurring-tasks", json=task1_data)
    client.post("/api/recurring-tasks", json=task2_data)
    
    # Act
    response = client.get("/api/recurring-tasks")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least the two we just created
    assert "X-Correlation-ID" in response.headers


# VALIDATION ERROR TESTS (422 status)

def test_create_recurring_task_empty_name_validation(client):
    """Test validation error when task name is empty"""
    # Arrange
    person_data = {"name": "Test", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    invalid_data = {
        "task_name": "",  # Empty name
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_recurring_task_name_too_long_validation(client):
    """Test validation error when task name exceeds 30 characters"""
    # Arrange
    person_data = {"name": "Test", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    invalid_data = {
        "task_name": "This task name is way too long for validation and exceeds thirty characters",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_recurring_task_invalid_frequency(client):
    """Test validation error for invalid frequency"""
    # Arrange
    person_data = {"name": "Test", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    invalid_data = {
        "task_name": "Test Task",
        "assigned_to": member_id,
        "frequency": "Hourly",  # Invalid frequency
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_recurring_task_invalid_category(client):
    """Test validation error for invalid category"""
    # Arrange
    person_data = {"name": "Test", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    invalid_data = {
        "task_name": "Test Task",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Shopping",  # Invalid category
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_recurring_task_invalid_overdue_when(client):
    """Test validation error for invalid overdue_when"""
    # Arrange
    person_data = {"name": "Test", "member_type": "Person", "status": "Active"}
    member_response = client.post("/api/family-members", json=person_data)
    member_id = member_response.json()["member_id"]
    
    invalid_data = {
        "task_name": "Test Task",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "2 hours",  # Invalid overdue_when
        "category": "Medication",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# NOT FOUND TESTS (404 status)

def test_get_recurring_task_not_found(client):
    """Test 404 when recurring task doesn't exist"""
    # Arrange
    fake_id = "non-existent-task-uuid-12345"
    
    # Act
    response = client.get(f"/api/recurring-tasks/{fake_id}")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "Recurring task not found"
    assert "X-Correlation-ID" in response.headers


# MALFORMED REQUEST TESTS

def test_create_recurring_task_missing_required_fields(client):
    """Test validation error when required fields are missing"""
    # Arrange
    invalid_data = {
        "task_name": "Test Task"
        # Missing all other required fields
    }
    
    # Act
    response = client.post("/api/recurring-tasks", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_recurring_task_invalid_json(client):
    """Test error when sending invalid JSON"""
    # Act
    response = client.post(
        "/api/recurring-tasks",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 422  # FastAPI handles JSON parsing errors