"""
Tests for health check endpoints
"""
import pytest

def test_health_check_returns_200(client):
    """Test that health check endpoint returns 200 status"""
    response = client.get("/api/health")
    assert response.status_code == 200

def test_health_check_returns_expected_structure(client):
    """Test that health check returns expected JSON structure"""
    response = client.get("/api/health")
    data = response.json()
    
    assert "status" in data
    assert "app" in data
    assert "stage" in data
    assert "message" in data
    assert data["status"] == "healthy"

def test_hello_endpoint(client):
    """Test that hello endpoint works with name parameter"""
    response = client.get("/api/hello/test")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "test" in data["message"]