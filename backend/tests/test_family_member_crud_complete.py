# backend/tests/test_family_member_crud_complete.py
"""
TDD: Complete Family Member CRUD Tests - UPDATE and DELETE endpoints
Following TDD: Red → Green → Refactor
Following Best-practices.md: FastAPI TestClient, structured logging, error handling
"""
import pytest
from fastapi.testclient import TestClient


def test_update_family_member_success(client):
    """Test successful family member update via PUT endpoint"""
    # Arrange - Create a family member first
    create_data = {
        "name": "Original Bob",
        "member_type": "Person", 
        "status": "Active"
    }
    create_response = client.post("/api/family-members", json=create_data)
    assert create_response.status_code == 201
    member_id = create_response.json()["member_id"]
    
    # Update data
    update_data = {
        "name": "Updated Bob",
        "member_type": "Person",
        "status": "Inactive"
    }
    
    # Act
    response = client.put(f"/api/family-members/{member_id}", json=update_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == member_id
    assert data["name"] == "Updated Bob"
    assert data["status"] == "Inactive"
    assert "updated_at" in data
    assert "X-Correlation-ID" in response.headers


def test_update_family_member_pet_type_change(client):
    """Test updating member from Person to Pet with pet_type"""
    # Arrange - Create person first
    create_data = {
        "name": "Bob",
        "member_type": "Person",
        "status": "Active"
    }
    create_response = client.post("/api/family-members", json=create_data)
    member_id = create_response.json()["member_id"]
    
    # Update to Pet
    update_data = {
        "name": "Bob the Dog",
        "member_type": "Pet",
        "pet_type": "dog",
        "status": "Active"
    }
    
    # Act
    response = client.put(f"/api/family-members/{member_id}", json=update_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["member_type"] == "Pet"
    assert data["pet_type"] == "dog"
    assert data["name"] == "Bob the Dog"


def test_update_family_member_not_found(client):
    """Test update with non-existent member ID"""
    update_data = {
        "name": "Ghost Member",
        "member_type": "Person",
        "status": "Active"
    }
    
    # Act
    response = client.put("/api/family-members/non-existent-id", json=update_data)
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_update_family_member_validation_error(client):
    """Test update with invalid data"""
    # Arrange - Create member first
    create_data = {
        "name": "Bob",
        "member_type": "Person",
        "status": "Active"
    }
    create_response = client.post("/api/family-members", json=create_data)
    member_id = create_response.json()["member_id"]
    
    # Invalid update data (empty name)
    update_data = {
        "name": "",
        "member_type": "Person",
        "status": "Active"
    }
    
    # Act
    response = client.put(f"/api/family-members/{member_id}", json=update_data)
    
    # Assert
    assert response.status_code == 422


def test_delete_family_member_success(client):
    """Test successful family member deletion"""
    # Arrange - Create a family member first
    create_data = {
        "name": "To Be Deleted",
        "member_type": "Person",
        "status": "Active"
    }
    create_response = client.post("/api/family-members", json=create_data)
    member_id = create_response.json()["member_id"]
    
    # Act
    response = client.delete(f"/api/family-members/{member_id}")
    
    # Assert
    assert response.status_code == 204  # No Content for successful deletion
    
    # Verify member is actually deleted
    get_response = client.get(f"/api/family-members/{member_id}")
    assert get_response.status_code == 404


def test_delete_family_member_not_found(client):
    """Test delete with non-existent member ID"""
    # Act
    response = client.delete("/api/family-members/non-existent-id")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_delete_family_member_with_recurring_tasks_prevention(client):
    """Test that deleting family member with associated tasks is prevented"""
    # Arrange - Create family member and recurring task
    member_data = {
        "name": "Bob",
        "member_type": "Person",
        "status": "Active"
    }
    member_response = client.post("/api/family-members", json=member_data)
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
    client.post("/api/recurring-tasks", json=task_data)
    
    # Act - Try to delete member with associated tasks
    response = client.delete(f"/api/family-members/{member_id}")
    
    # Assert - Should be prevented
    assert response.status_code == 409  # Conflict
    data = response.json()
    assert "associated tasks" in data["detail"].lower()

