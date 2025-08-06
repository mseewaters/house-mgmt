"""
Weather Update Lambda Handler - Fetch raw OpenWeather data and cache in S3
Following Best-practices.md: Lambda handlers, structured logging, error handling, UTC timestamps
Triggered by EventBridge every 30 minutes to fetch fresh weather data from OpenWeather API
"""
import json
import os
import boto3
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from botocore.exceptions import ClientError
from utils.logging import log_info, log_error


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for scheduled weather data updates
    
    Triggered by: EventBridge scheduled rule (every 30 minutes)
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context object
        
    Returns:
        Dict with statusCode, body containing update results
        
    Process:
        1. Get API key from Parameter Store
        2. Call OpenWeather OneCall API with exact parameters you provided
        3. Save raw JSON response to S3 (no transformation)
        4. Log execution details and return success/failure
    """
    request_id = getattr(context, 'aws_request_id', 'unknown')
    start_time = datetime.now(timezone.utc)
    
    try:
        log_info(
            "weather_update_lambda_started",
            request_id=request_id,
            event_source=event.get('source'),
            trigger_time=start_time.isoformat()
        )
        
        # Get configuration from environment
        bucket_name = os.getenv('S3_WEATHER_BUCKET')
        if not bucket_name:
            raise ValueError("S3_WEATHER_BUCKET environment variable not set")
        
        # Get API key from Parameter Store
        api_key = get_openweather_api_key()
        
        log_info(
            "weather_update_configuration",
            bucket_name=bucket_name,
            has_api_key=bool(api_key and api_key != 'test-key'),
            request_id=request_id
        )
        
        # Fetch raw weather data from OpenWeather API
        weather_data = fetch_openweather_data(api_key)
        
        if weather_data:
            # Save raw JSON to S3
            save_weather_to_s3(bucket_name, weather_data, request_id)
            
            # Calculate execution time
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()
            
            log_info(
                "weather_update_completed_successfully",
                request_id=request_id,
                execution_time_seconds=execution_time,
                data_size_bytes=len(json.dumps(weather_data))
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Weather data updated successfully',
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'execution_time_seconds': execution_time,
                    'request_id': request_id
                })
            }
        else:
            log_error(
                "weather_update_api_failed",
                error="OpenWeather API returned no data",
                request_id=request_id
            )
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'message': 'Failed to fetch weather data from OpenWeather API',
                    'request_id': request_id
                })
            }
            
    except Exception as e:
        log_error(
            "weather_update_lambda_error",
            error=str(e),
            error_type=type(e).__name__,
            request_id=request_id
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'message': 'Weather update Lambda error',
                'error_type': type(e).__name__,
                'request_id': request_id
            })
        }


def get_openweather_api_key() -> str:
    """Get OpenWeather API key from AWS Parameter Store"""
    try:
        ssm_client = boto3.client('ssm', region_name='us-east-1')
        
        response = ssm_client.get_parameter(
            Name='/house-mgmt/openweather-api-key',
            WithDecryption=True
        )
        
        api_key = response['Parameter']['Value']
        log_info("OpenWeather API key retrieved from Parameter Store")
        return api_key
        
    except ClientError as e:
        log_error(f"Failed to get API key from Parameter Store: {e}")
        raise RuntimeError("Could not retrieve OpenWeather API key")
    except Exception as e:
        log_error(f"Unexpected error getting API key: {e}")
        raise RuntimeError("Could not retrieve OpenWeather API key")


def fetch_openweather_data(api_key: str) -> Dict[str, Any]:
    """
    Fetch raw weather data from OpenWeather OneCall API
    Uses exact API call format you provided
    """
    try:
        # Use your exact API call parameters
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            'lat': 40.3026,
            'lon': -74.5112,
            'exclude': 'current,minutely,hourly,alerts',
            'appid': api_key,
            'units': 'imperial'
        }
        
        log_info(
            "fetching_weather_from_openweather",
            url=url,
            lat=params['lat'],
            lon=params['lon']
        )
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        weather_data = response.json()
        
        # Add metadata to the response
        weather_data['fetched_at'] = datetime.now(timezone.utc).isoformat()
        weather_data['api_version'] = '3.0'
        
        log_info(
            "openweather_api_success",
            status_code=response.status_code,
            data_size=len(json.dumps(weather_data))
        )
        
        return weather_data
        
    except requests.exceptions.RequestException as e:
        log_error(f"OpenWeather API request failed: {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error fetching weather: {e}")
        return None


def save_weather_to_s3(bucket_name: str, weather_data: Dict[str, Any], request_id: str) -> None:
    """Save raw weather data to S3"""
    try:
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Save raw OpenWeather response
        s3_client.put_object(
            Bucket=bucket_name,
            Key='openweather-raw.json',
            Body=json.dumps(weather_data, indent=2),
            ContentType='application/json',
            Metadata={
                'updated_by': 'weather-update-lambda',
                'request_id': request_id
            }
        )
        
        log_info(
            "weather_data_saved_to_s3",
            bucket=bucket_name,
            key='openweather-raw.json',
            request_id=request_id
        )
        
    except Exception as e:
        log_error(
            "s3_save_failed",
            error=str(e),
            bucket=bucket_name,
            request_id=request_id
        )
        raise