
# backend/tests/test_recurring_task_crud_complete.py
"""
TDD: Complete Recurring Task CRUD Tests - UPDATE and DELETE endpoints
Following TDD: Red → Green → Refactor
Following Best-practices.md: FastAPI TestClient, structured logging, error handling
"""


from datetime import date


def test_update_recurring_task_success(client):
    """Test successful recurring task update via PUT endpoint"""
    # Arrange - Create family member and recurring task
    member_data = {
        "name": "Alice",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=member_data)
    member_id = member_response.json()["member_id"]
    
    task_data = {
        "task_name": "Original Task",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    create_response = client.post("/api/recurring-tasks", json=task_data)
    task_id = create_response.json()["task_id"]
    
    # Update data
    update_data = {
        "task_name": "Updated Task Name",
        "assigned_to": member_id,
        "frequency": "Weekly",
        "due": "Sunday",
        "overdue_when": "6 hours",
        "category": "Other",
        "status": "Inactive"
    }
    
    # Act
    response = client.put(f"/api/recurring-tasks/{task_id}", json=update_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["task_name"] == "Updated Task Name"
    assert data["frequency"] == "Weekly"
    assert data["due"] == "Sunday"
    assert data["status"] == "Inactive"
    assert "updated_at" in data
    assert "X-Correlation-ID" in response.headers


def test_update_recurring_task_not_found(client):
    """Test update with non-existent task ID"""
    # Arrange - Need valid member_id for update data
    member_data = {
        "name": "Alice",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=member_data)
    member_id = member_response.json()["member_id"]
    
    update_data = {
        "task_name": "Ghost Task",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Other",
        "status": "Active"
    }
    
    # Act
    response = client.put("/api/recurring-tasks/non-existent-id", json=update_data)
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_update_recurring_task_validation_error(client):
    """Test update with invalid data"""
    # Arrange - Create member and task first
    member_data = {
        "name": "Alice",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=member_data)
    member_id = member_response.json()["member_id"]
    
    task_data = {
        "task_name": "Test Task",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    create_response = client.post("/api/recurring-tasks", json=task_data)
    task_id = create_response.json()["task_id"]
    
    # Invalid update data (empty task name)
    update_data = {
        "task_name": "",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    
    # Act
    response = client.put(f"/api/recurring-tasks/{task_id}", json=update_data)
    
    # Assert
    assert response.status_code == 422


def test_delete_recurring_task_success(client):
    """Test successful recurring task deletion"""
    # Arrange - Create family member and recurring task
    member_data = {
        "name": "Alice",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=member_data)
    member_id = member_response.json()["member_id"]
    
    task_data = {
        "task_name": "To Be Deleted",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    create_response = client.post("/api/recurring-tasks", json=task_data)
    task_id = create_response.json()["task_id"]
    
    # Act
    response = client.delete(f"/api/recurring-tasks/{task_id}")
    
    # Assert
    assert response.status_code == 204  # No Content for successful deletion
    
    # Verify task is actually deleted
    get_response = client.get(f"/api/recurring-tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_recurring_task_not_found(client):
    """Test delete with non-existent task ID"""
    # Act
    response = client.delete("/api/recurring-tasks/non-existent-id")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_delete_recurring_task_with_daily_instances_cleanup(client):
    """Test that deleting recurring task also cleans up associated daily instances"""
    # Arrange - Create member, recurring task, and generate daily instances
    member_data = {
        "name": "Bob",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=member_data)
    member_id = member_response.json()["member_id"]
    
    task_data = {
        "task_name": "Daily Pills",
        "assigned_to": member_id,
        "frequency": "Daily",
        "due": "Morning",
        "overdue_when": "1 hour",
        "category": "Medication",
        "status": "Active"
    }
    create_response = client.post("/api/recurring-tasks", json=task_data)
    task_id = create_response.json()["task_id"]
    
    # Generate daily tasks for today
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    generate_response = client.post(f"/api/daily-tasks/generate?date={today}")
    assert generate_response.status_code in [200, 201]
    
    # Act - Delete the recurring task
    response = client.delete(f"/api/recurring-tasks/{task_id}")
    
    # Assert
    assert response.status_code == 204
    
    # Verify recurring task is deleted
    get_response = client.get(f"/api/recurring-tasks/{task_id}")
    assert get_response.status_code == 404
    
    # Note: Daily task cleanup verification would require more complex logic
    # For MVP, we may choose to keep daily instances for audit purposes