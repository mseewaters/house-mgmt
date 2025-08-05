"""
TDD: Weather Update Lambda Tests - Background weather data fetching
Following TDD: Red → Green → Refactor
Following Best-practices.md: Lambda handlers, Parameter Store, S3 operations
ALL TESTS USE @mock_aws for consistent mocking
"""
import pytest
from moto import mock_aws
import boto3
import json
import requests
from datetime import datetime, timezone
from unittest.mock import patch, Mock


@mock_aws
def test_weather_update_lambda_fetches_and_saves_to_s3():
    """Test Lambda fetches OpenWeather data and saves raw JSON to S3 - WILL FAIL until Lambda exists"""
    # Arrange - Create mock S3 bucket and Parameter Store
    s3 = boto3.client('s3', region_name='us-east-1')
    ssm = boto3.client('ssm', region_name='us-east-1')
    
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    # Mock Parameter Store with API key
    ssm.put_parameter(
        Name='/house-mgmt/openweather-api-key',
        Value='test-api-key-12345',
        Type='SecureString'
    )
    
    # Mock EventBridge event
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = Mock()
    context.aws_request_id = 'test-weather-update'
    
    import os
    os.environ['S3_WEATHER_BUCKET'] = bucket_name
    
    # Mock the OpenWeather API response (using your exact JSON structure)
    mock_openweather_response = {
        "lat": 40.3026,
        "lon": -74.5112,
        "timezone": "America/New_York", 
        "timezone_offset": -14400,
        "daily": [
            {
                "dt": 1754413200,
                "temp": {"day": 83.3, "min": 63.52, "max": 83.44, "night": 70.05},
                "weather": [{"id": 804, "main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
                "humidity": 59,
                "wind_speed": 10.33
            },
            {
                "dt": 1754499600,
                "temp": {"day": 81.81, "min": 65.23, "max": 82.13, "night": 69.84},
                "weather": [{"id": 804, "main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
                "humidity": 51,
                "wind_speed": 11.23
            }
        ]
    }
    
    # Mock requests.get call to OpenWeather API
    with patch('lambdas.weather_update_handler.requests.get') as mock_requests:
        mock_response = Mock()
        mock_response.json.return_value = mock_openweather_response
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        from lambdas.weather_update_handler import lambda_handler
        
        # Act
        response = lambda_handler(event, context)
        
        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'updated_at' in body
        
        # Verify raw data was saved to S3
        s3_response = s3.get_object(Bucket=bucket_name, Key='openweather-raw.json')
        saved_data = json.loads(s3_response['Body'].read())
        
        # Verify it's the raw OpenWeather data plus metadata
        assert saved_data['lat'] == 40.3026
        assert saved_data['lon'] == -74.5112
        assert len(saved_data['daily']) == 2
        assert 'fetched_at' in saved_data
        assert saved_data['api_version'] == '3.0'


@mock_aws
def test_weather_update_lambda_handles_parameter_store_error():
    """Test Lambda handles Parameter Store errors gracefully - WILL FAIL until Lambda exists"""
    # Arrange - S3 bucket exists but no Parameter Store parameter
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = Mock()
    context.aws_request_id = 'test-parameter-store-error'
    
    import os
    os.environ['S3_WEATHER_BUCKET'] = bucket_name
    
    from lambdas.weather_update_handler import lambda_handler
    
    # Act
    response = lambda_handler(event, context)
    
    # Assert
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['success'] is False
    assert body['error_type'] == 'RuntimeError'
    # The actual Parameter Store error gets wrapped in the generic error handler


@mock_aws
def test_weather_update_lambda_handles_openweather_api_error():
    """Test Lambda handles OpenWeather API failures gracefully - WILL FAIL until Lambda exists"""
    # Arrange
    s3 = boto3.client('s3', region_name='us-east-1')
    ssm = boto3.client('ssm', region_name='us-east-1')
    
    bucket_name = 'house-mgmt-weather-test'
    s3.create_bucket(Bucket=bucket_name)
    
    ssm.put_parameter(
        Name='/house-mgmt/openweather-api-key',
        Value='test-api-key',
        Type='SecureString'
    )
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = Mock()
    context.aws_request_id = 'test-api-error'
    
    import os
    os.environ['S3_WEATHER_BUCKET'] = bucket_name
    
    # Mock API failure
    with patch('lambdas.weather_update_handler.requests.get') as mock_requests:
        mock_requests.side_effect = requests.exceptions.RequestException("API Error")
        
        from lambdas.weather_update_handler import lambda_handler
        
        # Act
        response = lambda_handler(event, context)
        
        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False


@mock_aws
def test_weather_update_lambda_handles_s3_error():
    """Test Lambda handles S3 save errors gracefully - WILL FAIL until Lambda exists"""
    # Arrange - Parameter Store exists but S3 bucket doesn't
    ssm = boto3.client('ssm', region_name='us-east-1')
    ssm.put_parameter(
        Name='/house-mgmt/openweather-api-key',
        Value='test-api-key',
        Type='SecureString'
    )
    
    event = {"source": ["aws.events"], "detail-type": ["Scheduled Event"]}
    context = Mock()
    context.aws_request_id = 'test-s3-error'
    
    import os
    os.environ['S3_WEATHER_BUCKET'] = 'non-existent-bucket'
    
    # Mock successful API call
    mock_response = Mock()
    mock_response.json.return_value = {"daily": [{"dt": 1754413200}]}
    mock_response.raise_for_status.return_value = None
    
    with patch('lambdas.weather_update_handler.requests.get', return_value=mock_response):
        from lambdas.weather_update_handler import lambda_handler
        
        # Act
        response = lambda_handler(event, context)
        
        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False