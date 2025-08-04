"""
TDD: Weather API Tests - REST endpoint for weather data
Following TDD: Red → Green → Refactor
Following existing API patterns from daily_task and other routes
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
import boto3
import json
from unittest.mock import patch


@mock_aws
def test_get_weather_success():
    """Test GET /api/weather returns current weather and forecast - WILL FAIL until endpoint exists"""
    # Arrange - Create mock S3 bucket with weather data
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Mock cached weather data
    weather_data = {
        "current": {
            "temperature": 78,
            "humidity": 62,
            "wind_speed": 8,
            "condition": "Clear",
            "icon": "01d"
        },
        "today": {
            "high": 83,
            "low": 65,
            "condition": "Clear", 
            "icon": "01d"
        },
        "forecast": [
            {"day": "Sunday", "high": 83, "low": 65, "icon": "01d", "condition": "Clear"},
            {"day": "Monday", "high": 86, "low": 68, "icon": "02d", "condition": "Few Clouds"},
            {"day": "Tuesday", "high": 84, "low": 66, "icon": "02d", "condition": "Few Clouds"},
            {"day": "Wednesday", "high": 82, "low": 64, "icon": "10d", "condition": "Rain"},
            {"day": "Thursday", "high": 79, "low": 61, "icon": "04d", "condition": "Overcast"}
        ],
        "updated_at": "2024-08-02T15:00:00Z"
    }
    
    # Store in S3
    s3.put_object(
        Bucket=bucket_name,
        Key='current-weather.json',
        Body=json.dumps(weather_data),
        ContentType='application/json'
    )
    
    # Set up FastAPI client with test configuration
    import os
    os.environ['WEATHER_CACHE_BUCKET'] = bucket_name
    
    from main import app
    client = TestClient(app)
    
    # Act - GET weather data
    response = client.get("/api/weather")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify current weather
    assert data["current"]["temperature"] == 78
    assert data["current"]["humidity"] == 62
    assert data["current"]["condition"] == "Clear"
    
    # Verify today's weather
    assert data["today"]["high"] == 83
    assert data["today"]["low"] == 65
    
    # Verify 5-day forecast
    assert len(data["forecast"]) == 5
    assert data["forecast"][0]["day"] == "Sunday"
    assert data["forecast"][4]["day"] == "Thursday"
    
    # Verify metadata
    assert "updated_at" in data


@mock_aws
def test_get_weather_cache_miss_fetches_from_api():
    """Test weather API fetches from OpenWeather when cache is empty - WILL FAIL until implemented"""
    # Arrange - Empty S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    import os
    os.environ['WEATHER_CACHE_BUCKET'] = bucket_name
    os.environ['OPENWEATHER_API_KEY'] = 'test-api-key'
    
    from main import app
    client = TestClient(app)
    
    # Mock the weather service API call
    with patch('services.weather_service.WeatherService._fetch_from_openweather_api') as mock_fetch:
        mock_fetch.return_value = {
            "current": {"temperature": 75, "humidity": 58, "wind_speed": 6, "condition": "Cloudy", "icon": "03d"},
            "today": {"high": 79, "low": 62, "condition": "Cloudy", "icon": "03d"},
            "forecast": [
                {"day": "Friday", "high": 79, "low": 62, "icon": "03d", "condition": "Cloudy"},
                {"day": "Saturday", "high": 81, "low": 64, "icon": "01d", "condition": "Clear"},
                {"day": "Sunday", "high": 78, "low": 60, "icon": "10d", "condition": "Rain"},
                {"day": "Monday", "high": 76, "low": 58, "icon": "04d", "condition": "Overcast"},
                {"day": "Tuesday", "high": 80, "low": 63, "icon": "02d", "condition": "Few Clouds"}
            ]
        }
        
        # Act
        response = client.get("/api/weather")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["current"]["temperature"] == 75
        assert mock_fetch.called


def test_get_weather_service_error_returns_500():
    """Test weather API returns 500 when weather service fails - WILL FAIL until implemented"""
    import os
    os.environ['WEATHER_CACHE_BUCKET'] = 'non-existent-bucket'
    
    from main import app
    client = TestClient(app)
    
    # Mock weather service to raise exception
    with patch('services.weather_service.WeatherService.get_current_weather') as mock_weather:
        mock_weather.side_effect = Exception("Weather service error")
        
        # Act
        response = client.get("/api/weather")
        
        # Assert
        assert response.status_code == 500
        assert "error occurred while retrieving weather data" in response.text.lower()


def test_get_weather_no_data_available_returns_503():
    """Test weather API returns 503 when no weather data available - WILL FAIL until implemented"""
    import os
    os.environ['WEATHER_CACHE_BUCKET'] = 'empty-bucket'
    
    from main import app
    client = TestClient(app)
    
    # Mock weather service to return None (no data available)
    with patch('services.weather_service.WeatherService.get_current_weather') as mock_weather:
        mock_weather.return_value = None
        
        # Act
        response = client.get("/api/weather")
        
        # Assert
        assert response.status_code == 503
        assert "weather data is currently unavailable" in response.text.lower()


@mock_aws
def test_weather_api_includes_correlation_id():
    """Test weather API includes correlation ID in response headers - WILL FAIL until implemented"""
    # Arrange - Setup mock weather data
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    weather_data = {
        "current": {"temperature": 72, "humidity": 55, "wind_speed": 5, "condition": "Clear", "icon": "01d"},
        "today": {"high": 77, "low": 60, "condition": "Clear", "icon": "01d"},
        "forecast": [{"day": "Sunday", "high": 77, "low": 60, "icon": "01d", "condition": "Clear"}],
        "updated_at": "2024-08-02T16:00:00Z"
    }
    
    s3.put_object(
        Bucket=bucket_name,
        Key='current-weather.json',
        Body=json.dumps(weather_data),
        ContentType='application/json'
    )
    
    import os
    os.environ['WEATHER_CACHE_BUCKET'] = bucket_name
    
    from main import app
    client = TestClient(app)
    
    # Act
    response = client.get("/api/weather")
    
    # Assert
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    
    # Verify correlation ID format (should be UUID-like)
    correlation_id = response.headers["X-Correlation-ID"]
    assert len(correlation_id) > 10  # Basic sanity check