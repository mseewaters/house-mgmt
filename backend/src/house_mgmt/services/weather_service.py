"""
Weather Service - Transform raw OpenWeather data from S3 for frontend consumption
Following Best-practices.md: Service layer, structured logging, error handling
Reads raw OpenWeather JSON from S3 and transforms to frontend format
"""
import os
import json
import boto3
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
from house_mgmt.utils.logging import log_info, log_error


class WeatherService:
    """
    Service for weather data transformation and serving
    
    Responsibilities:
    - Read raw OpenWeather data from S3 cache
    - Transform raw JSON to frontend-friendly format
    - Handle cache validation and staleness
    - Provide fallback when data unavailable
    """
    
    def __init__(self, bucket_name: str = None) -> None:
        """
        Initialize weather service with S3 bucket for reading cached data
        
        Args:
            bucket_name: S3 bucket name for reading cached data
        """
        # Handle bucket name validation  
        if bucket_name is None:
            self.bucket_name = os.getenv('S3_WEATHER_BUCKET', 'house-mgmt-weather-data')
        else:
            if not bucket_name or not bucket_name.strip():
                raise ValueError("S3 bucket name is required")
            self.bucket_name = bucket_name.strip()
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3', region_name='us-east-1')
        except Exception as e:
            log_error("Failed to initialize S3 client", error=str(e))
            self.s3_client = None
        
        # Cache configuration
        self.cache_key = "openweather-raw.json"  # Raw data from update Lambda
        self.cache_expiry_minutes = 45  # Consider stale after 45 minutes
        
        log_info(
            "Weather service initialized",
            bucket_name=self.bucket_name,
            has_s3_client=self.s3_client is not None
        )
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current weather and 5-day forecast by reading and transforming S3 data
        
        Returns:
            Transformed weather data dict with current conditions and 5-day forecast, or None if error
            
        Process:
        1. Read raw OpenWeather JSON from S3 
        2. Transform to frontend format
        3. Check if data is stale (> 45 minutes old)
        4. Return formatted data or None if unavailable
        """
        try:
            log_info("Weather data request started")
            
            # Read raw data from S3
            raw_weather_data = self._get_raw_data_from_s3()
            if not raw_weather_data:
                log_error("No weather data available in S3 cache")
                return None
            
            # Check if data is stale
            if self._is_data_stale(raw_weather_data):
                log_info("Weather data is stale but returning anyway")
                # Still return stale data rather than nothing
            
            # Transform raw OpenWeather data to frontend format
            transformed_data = self._transform_openweather_data(raw_weather_data)
            
            log_info(
                "Weather data transformed successfully",
                forecast_days=len(transformed_data.get("forecast", [])),
                updated_at=transformed_data.get("updated_at")
            )
            
            return transformed_data
            
        except Exception as e:
            log_error("Failed to get weather data", error=str(e))
            return None
    
    def _get_raw_data_from_s3(self) -> Optional[Dict[str, Any]]:
        """Read raw OpenWeather JSON data from S3"""
        if not self.s3_client:
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.cache_key
            )
            
            raw_data = json.loads(response['Body'].read())
            log_info("Raw weather data retrieved from S3")
            return raw_data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                log_info("No cached weather data found in S3")
            else:
                log_error(f"S3 error retrieving weather data: {e}")
            return None
        except Exception as e:
            log_error(f"Unexpected error retrieving weather data: {e}")
            return None
    
    def _is_data_stale(self, weather_data: Dict[str, Any]) -> bool:
        """Check if weather data is considered stale (> 45 minutes old)"""
        try:
            fetched_at_str = weather_data.get('fetched_at')
            if not fetched_at_str:
                return True
            
            fetched_at = datetime.fromisoformat(fetched_at_str.replace('Z', '+00:00'))
            age_minutes = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 60
            
            return age_minutes > self.cache_expiry_minutes
            
        except Exception as e:
            log_error(f"Error checking data staleness: {e}")
            return True
    
    def _transform_openweather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw OpenWeather OneCall API response to frontend format
        
        Input: Raw OpenWeather 3.0 OneCall API response (daily data only)
        Output: Frontend-friendly format with current, today, and 5-day forecast
        """
        try:
            daily_data = raw_data.get('daily', [])
            if not daily_data:
                log_error("No daily data in OpenWeather response")
                return None
            
            # Today is the first day in the daily array
            today_data = daily_data[0]
            
            # Extract current weather (using today's data as proxy for current)
            current = {
                "temperature": round(today_data['temp']['day']),
                "humidity": today_data['humidity'],
                "wind_speed": round(today_data['wind_speed']),
                "condition": today_data['weather'][0]['description'].title(),
                "icon": today_data['weather'][0]['icon']
            }
            
            # Extract today's high/low
            today = {
                "high": round(today_data['temp']['max']),
                "low": round(today_data['temp']['min']),
                "condition": today_data['weather'][0]['description'].title(),
                "icon": today_data['weather'][0]['icon']
            }
            
            # Extract 5-day forecast (skip today, take next 5 days)
            forecast = []
            for i, day_data in enumerate(daily_data[1:6]):  # Skip today, take next 5
                day_timestamp = day_data['dt']
                day_name = datetime.fromtimestamp(day_timestamp, tz=timezone.utc).strftime('%A')
                
                forecast.append({
                    "day": day_name,
                    "high": round(day_data['temp']['max']),
                    "low": round(day_data['temp']['min']),
                    "icon": day_data['weather'][0]['icon'],
                    "condition": day_data['weather'][0]['description'].title()
                })
            
            # Create final response
            transformed_data = {
                "current": current,
                "today": today,
                "forecast": forecast,
                "updated_at": raw_data.get('fetched_at', datetime.now(timezone.utc).isoformat())
            }
            
            log_info(
                "Weather data transformation completed",
                current_temp=current['temperature'],
                today_high=today['high'],
                forecast_days=len(forecast)
            )
            
            return transformed_data
            
        except (KeyError, IndexError, TypeError) as e:
            log_error(f"Error transforming weather data: {e}")
            return None
        except Exception as e:
            log_error(f"Unexpected error in weather transformation: {e}")
            return None