"""
TDD: Weather API Tests - REST endpoint for weather data (UPDATED for S3 architecture)
Following TDD: Red → Green → Refactor
Following new architecture: Weather service reads raw data from S3 and transforms
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
import boto3
import json
from datetime import datetime, timezone


@mock_aws
def test_get_weather_success():
    """Test GET /api/weather returns transformed weather data from S3 - WILL FAIL until service updated"""
    # Arrange - Create mock S3 bucket with raw OpenWeather data
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Mock raw OpenWeather data (your format)
    raw_openweather_data = {
        "lat": 40.3026,
        "lon": -74.5112,
        "timezone": "America/New_York",
        "timezone_offset": -14400,
        "daily": [
            {
                "dt": 1754413200,
                "temp": {"day": 83.3, "min": 63.52, "max": 83.44, "night": 70.05},
                "humidity": 59,
                "wind_speed": 10.33,
                "weather": [{"id": 804, "main": "Clouds", "description": "overcast clouds", "icon": "04d"}]
            },
            {
                "dt": 1754499600,
                "temp": {"day": 81.81, "min": 65.23, "max": 82.13, "night": 69.84},
                "humidity": 51,
                "wind_speed": 11.23,
                "weather": [{"id": 804, "main": "Clouds", "description": "overcast clouds", "icon": "04d"}]
            },
            {
                "dt": 1754586000,
                "temp": {"day": 80.35, "min": 64.74, "max": 80.8, "night": 64.74},
                "humidity": 47,
                "wind_speed": 13.06,
                "weather": [{"id": 802, "main": "Clouds", "description": "scattered clouds", "icon": "03d"}]
            }
        ],
        "fetched_at": "2024-08-04T15:30:00Z",
        "api_version": "3.0"
    }
    
    # Store raw data in S3
    s3.put_object(
        Bucket=bucket_name,
        Key='openweather-raw.json',
        Body=json.dumps(raw_openweather_data),
        ContentType='application/json'
    )
    
    # Set up FastAPI client with test configuration
    import os
    os.environ['S3_WEATHER_BUCKET'] = bucket_name
    
    from main import app
    client = TestClient(app)
    
    # Act - GET weather data
    response = client.get("/api/weather")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify current weather (should use today's data)
    assert data["current"]["temperature"] == 83  # Rounded from 83.3
    assert data["current"]["humidity"] == 59
    assert data["current"]["wind_speed"] == 10  # Rounded from 10.33
    assert data["current"]["condition"] == "Overcast Clouds"
    assert data["current"]["icon"] == "04d"
    
    # Verify today's weather (should use today's max/min)
    assert data["today"]["high"] == 83  # Rounded from 83.44
    assert data["today"]["low"] == 64   # Rounded from 63.52
    assert data["today"]["condition"] == "Overcast Clouds"
    assert data["today"]["icon"] == "04d"
    
    # Verify forecast (should skip today, take next days)
    assert len(data["forecast"]) >= 2  # At least 2 forecast days from our mock data
    
    # Verify metadata
    assert data["updated_at"] == "2024-08-04T15:30:00Z"


@mock_aws
def test_get_weather_handles_missing_s3_data():
    """Test weather API handles missing S3 data gracefully - WILL FAIL until service updated"""
    # Arrange - Empty S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    import os
    os.environ['S3_WEATHER_BUCKET'] = bucket_name
    
    from main import app
    client = TestClient(app)
    
    # Act
    response = client.get("/api/weather")
    
    # Assert
    assert response.status_code == 503
    data = response.json()
    assert "Weather data is currently unavailable" in data["detail"]


@mock_aws
def test_weather_api_includes_correlation_id():
    """Test weather API includes correlation ID in response headers - WILL FAIL until service updated"""
    # Arrange - Create S3 bucket with minimal weather data
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    minimal_weather_data = {
        "daily": [
            {
                "dt": 1754413200,
                "temp": {"day": 75, "min": 60, "max": 80},
                "humidity": 50,
                "wind_speed": 8,
                "weather": [{"description": "clear sky", "icon": "01d"}]
            }
        ],
        "fetched_at": "2024-08-04T15:30:00Z",
        "api_version": "3.0"
    }
    
    s3.put_object(
        Bucket=bucket_name,
        Key='openweather-raw.json',
        Body=json.dumps(minimal_weather_data),
        ContentType='application/json'
    )
    
    import os
    os.environ['S3_WEATHER_BUCKET'] = bucket_name
    
    from main import app
    client = TestClient(app)
    
    # Act
    response = client.get("/api/weather")
    
    # Assert
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers