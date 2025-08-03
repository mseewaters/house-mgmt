"""
Test Family Member API routes
Following TDD: Write failing tests first
"""
import pytest
import json

# HAPPY PATH TESTS

def test_create_family_member_person_success(client):
    """Test successful creation of a person family member"""
    # Arrange
    person_data = {
        "name": "Sarah",
        "member_type": "Person",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/family-members", json=person_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Sarah"
    assert data["member_type"] == "Person"
    assert data["status"] == "Active"
    assert data["pet_type"] is None
    assert "member_id" in data
    assert "created_at" in data
    assert "updated_at" in data
    # Verify correlation ID is in response headers
    assert "X-Correlation-ID" in response.headers


def test_create_family_member_pet_success(client):
    """Test successful creation of a pet family member"""
    # Arrange
    pet_data = {
        "name": "Buddy",
        "member_type": "Pet",
        "pet_type": "dog",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/family-members", json=pet_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Buddy"
    assert data["member_type"] == "Pet"
    assert data["pet_type"] == "dog"
    assert data["status"] == "Active"
    assert "member_id" in data
    assert "X-Correlation-ID" in response.headers


def test_get_family_member_success(client):
    """Test successful retrieval of family member by ID"""
    # Arrange - First create a family member
    person_data = {
        "name": "John",
        "member_type": "Person", 
        "status": "Active"
    }
    create_response = client.post("/api/family-members", json=person_data)
    created_member = create_response.json()
    member_id = created_member["member_id"]
    
    # Act
    response = client.get(f"/api/family-members/{member_id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == member_id
    assert data["name"] == "John"
    assert data["member_type"] == "Person"
    assert "X-Correlation-ID" in response.headers


def test_get_all_family_members_success(client):
    """Test successful retrieval of all family members"""
    # Arrange - Create a couple family members
    person_data = {"name": "Alice", "member_type": "Person", "status": "Active"}
    pet_data = {"name": "Max", "member_type": "Pet", "pet_type": "cat", "status": "Active"}
    
    client.post("/api/family-members", json=person_data)
    client.post("/api/family-members", json=pet_data)
    
    # Act
    response = client.get("/api/family-members")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least the two we just created
    assert "X-Correlation-ID" in response.headers


# VALIDATION ERROR TESTS (400 status)

def test_create_family_member_empty_name_validation(client):
    """Test validation error when name is empty"""
    # Arrange
    invalid_data = {
        "name": "",
        "member_type": "Person",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/family-members", json=invalid_data)
    
    # Assert
    assert response.status_code == 422  # Pydantic validation error
    data = response.json()
    assert "detail" in data
    # Should mention name validation issue
    assert any("name" in str(error).lower() for error in data["detail"])


def test_create_family_member_name_too_long_validation(client):
    """Test validation error when name exceeds 15 characters"""
    # Arrange
    invalid_data = {
        "name": "ThisNameIsTooLongForValidation",  # >15 chars
        "member_type": "Person",
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/family-members", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_pet_without_pet_type_validation(client):
    """Test validation error when Pet missing pet_type"""
    # Arrange
    invalid_data = {
        "name": "Buddy",
        "member_type": "Pet",
        "status": "Active"
        # Missing pet_type - should cause validation error
    }
    
    # Act
    response = client.post("/api/family-members", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_person_with_pet_type_validation(client):
    """Test validation error when Person has pet_type"""
    # Arrange
    invalid_data = {
        "name": "Sarah",
        "member_type": "Person",
        "pet_type": "dog",  # Should not be provided for Person
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/family-members", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_family_member_invalid_member_type(client):
    """Test validation error for invalid member_type"""
    # Arrange
    invalid_data = {
        "name": "Test",
        "member_type": "Robot",  # Invalid type
        "status": "Active"
    }
    
    # Act
    response = client.post("/api/family-members", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# NOT FOUND TESTS (404 status)

def test_get_family_member_not_found(client):
    """Test 404 when family member doesn't exist"""
    # Arrange
    fake_id = "non-existent-uuid-12345"
    
    # Act
    response = client.get(f"/api/family-members/{fake_id}")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "Family member not found"
    assert "X-Correlation-ID" in response.headers


# MALFORMED REQUEST TESTS (400 status)

def test_create_family_member_missing_required_fields(client):
    """Test validation error when required fields are missing"""
    # Arrange
    invalid_data = {
        "name": "Test"
        # Missing member_type and status
    }
    
    # Act
    response = client.post("/api/family-members", json=invalid_data)
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_family_member_invalid_json(client):
    """Test error when sending invalid JSON"""
    # Act
    response = client.post(
        "/api/family-members", 
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 422  # FastAPI handles JSON parsing errors