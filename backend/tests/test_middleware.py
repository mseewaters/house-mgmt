"""
Test correlation ID middleware functionality
Following TDD: Write failing tests first
"""
import pytest

def test_correlation_id_added_to_response_headers(client):
    """Test that correlation ID is added to response headers"""
    # Act
    response = client.get("/api/health")
    
    # Assert
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert len(response.headers["X-Correlation-ID"]) > 0
    # Should be UUID format (36 chars with dashes)
    corr_id = response.headers["X-Correlation-ID"]
    assert len(corr_id) == 36
    assert corr_id.count("-") == 4


def test_correlation_id_unique_per_request(client):
    """Test that each request gets a unique correlation ID"""
    # Act - Make multiple requests
    response1 = client.get("/api/health")
    response2 = client.get("/api/health")
    
    # Assert
    print(f"Response1 headers: {dict(response1.headers)}")
    print(f"Response2 headers: {dict(response2.headers)}")
    
    corr_id1 = response1.headers["X-Correlation-ID"]
    corr_id2 = response2.headers["X-Correlation-ID"]
    assert corr_id1 != corr_id2


def test_custom_correlation_id_preserved(client):
    """Test that custom correlation ID from request header is preserved"""
    custom_id = "custom-trace-12345"
    
    # Act
    response = client.get("/api/health", headers={"X-Correlation-ID": custom_id})
    
    # Assert
    print(f"Custom ID response headers: {dict(response.headers)}")
    assert response.headers["X-Correlation-ID"] == custom_id


def test_correlation_id_available_in_request_state(client):
    """Test that correlation ID is available in FastAPI request state"""
    # Act
    response = client.get("/api/test/correlation")
    
    # Assert
    print(f"Test endpoint response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["correlation_id"] is not None
    assert len(data["correlation_id"]) == 36  # UUID format