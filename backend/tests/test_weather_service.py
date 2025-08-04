"""
TDD: Weather Service Tests - OpenWeather API integration with S3 caching
Following TDD: Red → Green → Refactor
Following Best-practices.md: External API integration, caching, error handling
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime, timezone
from unittest.mock import patch, Mock
import json


@mock_aws
def test_get_current_weather_from_cache_success():
    """Test retrieving current weather from S3 cache - WILL FAIL until service exists"""
    # Arrange - Create mock S3 bucket with cached weather data
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Mock cached weather data with 5-day forecast
    cached_weather = {
        "current": {
            "temperature": 77,
            "humidity": 56,
            "wind_speed": 7,
            "condition": "Few Clouds",
            "icon": "02d"
        },
        "today": {
            "high": 82,
            "low": 60,
            "condition": "Few Clouds",
            "icon": "02d"
        },
        "forecast": [
            {"day": "Sunday", "high": 82, "low": 60, "icon": "01d", "condition": "Clear"},
            {"day": "Monday", "high": 86, "low": 61, "icon": "02d", "condition": "Few Clouds"},
            {"day": "Tuesday", "high": 84, "low": 64, "icon": "02d", "condition": "Few Clouds"},
            {"day": "Wednesday", "high": 85, "low": 65, "icon": "02d", "condition": "Few Clouds"},
            {"day": "Thursday", "high": 82, "low": 66, "icon": "11d", "condition": "Thunderstorm"}
        ],
        "updated_at": "2024-08-02T14:00:00Z"
    }
    
    # Store in S3
    s3.put_object(
        Bucket=bucket_name,
        Key='current-weather.json',
        Body=json.dumps(cached_weather),
        ContentType='application/json'
    )
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name)
    
    # Act
    result = weather_service.get_current_weather()
    
    # Assert
    assert result is not None
    assert result["current"]["temperature"] == 77
    assert result["current"]["humidity"] == 56
    assert result["today"]["high"] == 82
    assert len(result["forecast"]) == 5  # 5-day forecast
    assert result["forecast"][0]["day"] == "Sunday"
    assert result["forecast"][4]["day"] == "Thursday"  # 5th day
    assert result["forecast"][4]["condition"] == "Thunderstorm"


@mock_aws
def test_get_current_weather_cache_miss_fetches_from_api():
    """Test fetching weather from OpenWeather API when cache is empty - WILL FAIL until implemented"""
    # Arrange - Empty S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Mock OpenWeather API response
    mock_current_response = {
        "main": {"temp": 75.2, "humidity": 65},
        "wind": {"speed": 8.5},
        "weather": [{"main": "Clear", "icon": "01d", "description": "clear sky"}]
    }
    
    mock_forecast_response = {
        "list": [
            {
                "dt_txt": "2024-08-02 12:00:00",
                "main": {"temp_max": 80, "temp_min": 62},
                "weather": [{"main": "Clear", "icon": "01d"}]
            },
            {
                "dt_txt": "2024-08-03 12:00:00", 
                "main": {"temp_max": 85, "temp_min": 63},
                "weather": [{"main": "Clouds", "icon": "02d"}]
            }
        ]
    }
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name)
    
    # Mock the API calls
    with patch.object(weather_service, '_fetch_from_openweather_api') as mock_fetch:
        mock_fetch.return_value = {
            "current": {"temperature": 75, "humidity": 65, "wind_speed": 9, "condition": "Clear", "icon": "01d"},
            "today": {"high": 80, "low": 62, "condition": "Clear", "icon": "01d"},
            "forecast": [
                {"day": "Friday", "high": 80, "low": 62, "icon": "01d", "condition": "Clear"},
                {"day": "Saturday", "high": 85, "low": 63, "icon": "02d", "condition": "Clouds"},
                {"day": "Sunday", "high": 78, "low": 60, "icon": "10d", "condition": "Rain"},
                {"day": "Monday", "high": 82, "low": 65, "icon": "01d", "condition": "Clear"},
                {"day": "Tuesday", "high": 79, "low": 61, "icon": "04d", "condition": "Overcast"}
            ]
        }
        
        # Act
        result = weather_service.get_current_weather()
        
        # Assert
        assert result is not None
        assert result["current"]["temperature"] == 75
        assert len(result["forecast"]) == 5  # 5-day forecast
        assert mock_fetch.called
        
        # Verify data was cached in S3
        cached_object = s3.get_object(Bucket=bucket_name, Key='current-weather.json')
        cached_data = json.loads(cached_object['Body'].read())
        assert cached_data["current"]["temperature"] == 75
        assert len(cached_data["forecast"]) == 5


@mock_aws
def test_weather_service_api_key_validation():
    """Test weather service validates API key is provided when explicitly empty"""
    from services.weather_service import WeatherService
    
    # These should work (use defaults)
    service1 = WeatherService()  # Should use default
    assert service1.api_key in ['test-key', 'test-api-key']  # Allow either default
    
    service2 = WeatherService(api_key="valid-key")  # Should work
    assert service2.api_key == "valid-key"
    
    # These should fail (explicit empty values)
    with pytest.raises(ValueError, match="OpenWeather API key is required"):
        WeatherService(api_key="")
    
    with pytest.raises(ValueError, match="OpenWeather API key is required"):
        WeatherService(api_key="   ")  # Whitespace only


@mock_aws
def test_weather_service_handles_api_error_gracefully():
    """Test weather service handles OpenWeather API errors gracefully - WILL FAIL until implemented"""
    # Arrange
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name, api_key="test-key")
    
    # Mock API failure
    with patch.object(weather_service, '_fetch_from_openweather_api') as mock_fetch:
        mock_fetch.side_effect = Exception("API Error")
        
        # Act & Assert - Should handle error gracefully
        result = weather_service.get_current_weather()
        
        # Should return None or cached data, not raise exception
        assert result is None  # No cached data available


@mock_aws 
def test_weather_cache_expiry_logic():
    """Test weather cache respects expiry time (1 hour) - WILL FAIL until implemented"""
    # Arrange - Create S3 bucket with expired cache
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Create expired weather data (2 hours old)
    from datetime import timedelta
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    expired_weather = {
        "current": {"temperature": 70, "humidity": 50, "wind_speed": 5, "condition": "Old", "icon": "01d"},
        "updated_at": two_hours_ago.isoformat()
    }
    
    s3.put_object(
        Bucket=bucket_name,
        Key='current-weather.json',
        Body=json.dumps(expired_weather),
        ContentType='application/json'
    )
    
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(bucket_name=bucket_name, api_key="test-key")
    
    # Mock API call for fresh data
    with patch.object(weather_service, '_fetch_from_openweather_api') as mock_fetch:
        mock_fetch.return_value = {
            "current": {"temperature": 78, "humidity": 60, "wind_speed": 8, "condition": "Fresh", "icon": "02d"},
            "today": {"high": 82, "low": 65, "condition": "Fresh", "icon": "02d"},
            "forecast": []
        }
        
        # Act
        result = weather_service.get_current_weather()
        
        # Assert - Should fetch fresh data, not use expired cache
        assert result["current"]["temperature"] == 78  # Fresh data
        assert result["current"]["condition"] == "Fresh"
        assert mock_fetch.called


@mock_aws
def test_weather_data_transformation():
    """Test OpenWeather API response is properly transformed - WILL FAIL until implemented"""
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(api_key="test-key")
    
    # Mock raw OpenWeather API responses
    raw_current = {
        "main": {"temp": 76.5, "humidity": 58, "temp_max": 80.2, "temp_min": 62.8},
        "wind": {"speed": 7.2},
        "weather": [{"main": "Clouds", "icon": "03d", "description": "scattered clouds"}]
    }
    
    raw_forecast = {
        "list": [
            {
                "dt_txt": "2024-08-02 15:00:00",
                "main": {"temp_max": 79.8, "temp_min": 63.1},
                "weather": [{"main": "Clear", "icon": "01d", "description": "clear sky"}]
            }
        ]
    }
    
    # Act - Test internal transformation method
    result = weather_service._transform_weather_data(raw_current, raw_forecast)
    
    # Assert - Should transform to our standard format
    assert result["current"]["temperature"] == 76  # 76.5 rounds to 76
    assert result["current"]["humidity"] == 58
    assert result["current"]["wind_speed"] == 7  # 7.2 rounds to 7
    assert result["current"]["condition"] == "Clouds"
    assert result["current"]["icon"] == "03d"
    
    assert result["today"]["high"] == 80  # 80.2 rounds to 80 (from current data)
    assert result["today"]["low"] == 63   # 62.8 rounds to 63 (from current data)
    assert "updated_at" in result


@mock_aws
def test_weather_service_bucket_validation():
    """Test weather service validates S3 bucket configuration when explicitly empty"""
    from services.weather_service import WeatherService
    
    # These should work (use defaults)
    service1 = WeatherService()  # Should use default bucket
    assert 'house-mgmt-weather' in service1.bucket_name
    
    service2 = WeatherService(bucket_name="valid-bucket")  # Should work
    assert service2.bucket_name == "valid-bucket"
    
    # These should fail (explicit empty values)
    with pytest.raises(ValueError, match="S3 bucket name is required"):
        WeatherService(bucket_name="", api_key="test-key")
    
    with pytest.raises(ValueError, match="S3 bucket name is required"):
        WeatherService(bucket_name="   ", api_key="test-key")  # Whitespace only


@mock_aws
def test_weather_service_returns_exactly_five_day_forecast():
    """Test weather service always returns exactly 5-day forecast - WILL FAIL until implemented"""
    # Arrange - Mock OpenWeather API with more than 5 days of data
    from services.weather_service import WeatherService
    
    weather_service = WeatherService(api_key="test-key")
    
    # Mock raw forecast with 7 days of data (API returns more, we should limit to 5)
    raw_forecast = {
        "list": [
            {"dt_txt": "2024-08-02 12:00:00", "main": {"temp_max": 80, "temp_min": 60}, "weather": [{"main": "Clear", "icon": "01d"}]},
            {"dt_txt": "2024-08-03 12:00:00", "main": {"temp_max": 82, "temp_min": 61}, "weather": [{"main": "Clouds", "icon": "02d"}]},
            {"dt_txt": "2024-08-04 12:00:00", "main": {"temp_max": 78, "temp_min": 58}, "weather": [{"main": "Rain", "icon": "10d"}]},
            {"dt_txt": "2024-08-05 12:00:00", "main": {"temp_max": 83, "temp_min": 62}, "weather": [{"main": "Clear", "icon": "01d"}]},
            {"dt_txt": "2024-08-06 12:00:00", "main": {"temp_max": 79, "temp_min": 59}, "weather": [{"main": "Clouds", "icon": "03d"}]},
            {"dt_txt": "2024-08-07 12:00:00", "main": {"temp_max": 85, "temp_min": 63}, "weather": [{"main": "Clear", "icon": "01d"}]},  # 6th day - should be excluded
            {"dt_txt": "2024-08-08 12:00:00", "main": {"temp_max": 87, "temp_min": 65}, "weather": [{"main": "Clear", "icon": "01d"}]}   # 7th day - should be excluded
        ]
    }
    
    raw_current = {
        "main": {"temp": 75, "humidity": 55},
        "wind": {"speed": 8},
        "weather": [{"main": "Clear", "icon": "01d"}]
    }
    
    # Act
    result = weather_service._transform_weather_data(raw_current, raw_forecast)
    
    # Assert - Should return exactly 5 days in forecast
    assert len(result["forecast"]) == 5
    assert result["forecast"][0]["high"] == 80  # First day
    assert result["forecast"][4]["high"] == 79  # Fifth day (not 85 from 6th day)
    
    # Verify 6th and 7th days are not included
    forecast_highs = [day["high"] for day in result["forecast"]]
    assert 85 not in forecast_highs  # 6th day excluded
    assert 87 not in forecast_highs  # 7th day excluded