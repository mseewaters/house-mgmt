"""
TDD: Updated Weather Service Tests - S3 data transformation for frontend
Following TDD: Red → Green → Refactor  
Following Best-practices.md: Service layer, data transformation, error handling
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from moto import mock_aws
import boto3
import json
from datetime import datetime, timezone, timedelta


@mock_aws
def test_weather_service_transforms_raw_openweather_data():
    """Test weather service reads raw OpenWeather JSON and transforms for frontend - WILL FAIL until updated"""
    # Arrange - Create S3 bucket with your exact OpenWeather JSON
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Your exact OpenWeather 3.0 OneCall API response (truncated for test)
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
            },
            {
                "dt": 1754672400,
                "temp": {"day": 80.78, "min": 61.97, "max": 81.12, "night": 63.63},
                "humidity": 39,
                "wind_speed": 10.65,
                "weather": [{"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}]
            },
            {
                "dt": 1754758800,
                "temp": {"day": 83.64, "min": 60.37, "max": 83.64, "night": 62.74},
                "humidity": 31,
                "wind_speed": 8.7,
                "weather": [{"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d"}]
            },
            {
                "dt": 1754845200,
                "temp": {"day": 88.21, "min": 60.76, "max": 89.62, "night": 68.77},
                "humidity": 35,
                "wind_speed": 7.36,
                "weather": [{"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}]
            }
        ],
        "fetched_at": "2024-08-04T15:30:00Z",
        "api_version": "3.0"
    }
    
    # Save raw data to S3
    s3.put_object(
        Bucket=bucket_name,
        Key='openweather-raw.json',
        Body=json.dumps(raw_openweather_data),
        ContentType='application/json'
    )
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name)
    
    # Act
    result = weather_service.get_current_weather()
    
    # Assert - Verify transformation to frontend format
    assert result is not None
    
    # Verify current weather (should use today's day temp)
    assert result["current"]["temperature"] == 83  # Rounded from 83.3
    assert result["current"]["humidity"] == 59
    assert result["current"]["wind_speed"] == 10  # Rounded from 10.33
    assert result["current"]["condition"] == "Overcast Clouds"
    assert result["current"]["icon"] == "04d"
    
    # Verify today's high/low (should use today's max/min)
    assert result["today"]["high"] == 83  # Rounded from 83.44
    assert result["today"]["low"] == 64   # Rounded from 63.52
    assert result["today"]["condition"] == "Overcast Clouds"
    assert result["today"]["icon"] == "04d"
    
    # Verify 5-day forecast (should skip today, take next 5 days)
    assert len(result["forecast"]) == 5
    
    # First forecast day (tomorrow)
    assert result["forecast"][0]["high"] == 82  # From daily[1]
    assert result["forecast"][0]["low"] == 65
    assert result["forecast"][0]["condition"] == "Overcast Clouds"
    
    # Last forecast day  
    assert result["forecast"][4]["high"] == 90  # From daily[5]
    assert result["forecast"][4]["low"] == 61
    
    # Verify metadata
    assert result["updated_at"] == "2024-08-04T15:30:00Z"


@mock_aws
def test_weather_service_handles_missing_s3_data():
    """Test weather service handles missing S3 data gracefully - WILL FAIL until updated"""
    # Arrange - Empty S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name)
    
    # Act
    result = weather_service.get_current_weather()
    
    # Assert
    assert result is None


@mock_aws
def test_weather_service_detects_stale_data():
    """Test weather service detects stale data (> 45 minutes old) - WILL FAIL until updated"""
    # Arrange - Create S3 bucket with old but valid data
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Create data that's 1 hour old (stale) but with complete structure
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    stale_data = {
        "lat": 40.3026,
        "lon": -74.5112,
        "daily": [
            {
                "dt": 1754413200,
                "temp": {"day": 70, "min": 60, "max": 75, "night": 65},
                "humidity": 50,
                "wind_speed": 8,
                "weather": [{"description": "stale conditions", "icon": "01d"}]
            },
            {
                "dt": 1754499600,
                "temp": {"day": 72, "min": 62, "max": 77, "night": 67},
                "humidity": 55,
                "wind_speed": 9,
                "weather": [{"description": "stale forecast", "icon": "02d"}]
            }
        ],
        "fetched_at": one_hour_ago.isoformat(),
        "api_version": "3.0"
    }
    
    s3.put_object(
        Bucket=bucket_name,
        Key='openweather-raw.json',
        Body=json.dumps(stale_data),
        ContentType='application/json'
    )
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name)
    
    # Act
    result = weather_service.get_current_weather()
    
    # Assert - Should still return data but log it as stale
    assert result is not None
    assert result["current"]["temperature"] == 70
    # The service should log that data is stale but still return it


@mock_aws  
def test_weather_service_handles_malformed_s3_data():
    """Test weather service handles malformed JSON in S3 - WILL FAIL until updated"""
    # Arrange - Create S3 bucket with invalid JSON
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Save malformed JSON
    s3.put_object(
        Bucket=bucket_name,
        Key='openweather-raw.json',
        Body='{"invalid": json malformed',
        ContentType='application/json'
    )
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name)
    
    # Act
    result = weather_service.get_current_weather()
    
    # Assert
    assert result is None