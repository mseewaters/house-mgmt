"""
Weather Service - OpenWeather API integration with S3 caching
Following Best-practices.md: External API integration, caching, structured logging, error handling
Following technical design: 5-day forecast with hourly cache refresh
"""
import os
import json
import boto3
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from utils.logging import log_info, log_error


class WeatherService:
    """
    Service for weather data retrieval with OpenWeather API and S3 caching
    
    Responsibilities:
    - Fetch current weather and 5-day forecast from OpenWeather API
    - Cache weather data in S3 with 1-hour expiry
    - Handle API errors gracefully with fallback to cached data
    - Transform API responses to standardized format
    """
    
    def __init__(self, api_key: str = None, bucket_name: str = None) -> None:
        """
        Initialize weather service with API key and S3 bucket
        
        Args:
            api_key: OpenWeather API key (defaults to environment variable or 'test-key' for testing)
            bucket_name: S3 bucket name for caching (defaults to environment variable)
            
        Raises:
            ValueError: If required configuration is missing
        """
    def __init__(self, api_key: str = None, bucket_name: str = None) -> None:
        """
        Initialize weather service with API key and S3 bucket
        
        Args:
            api_key: OpenWeather API key (defaults to environment variable or 'test-key' for testing)
            bucket_name: S3 bucket name for caching (defaults to environment variable)
            
        Raises:
            ValueError: If required configuration is missing
        """
        # Handle API key validation - distinguish between None passed explicitly vs default
        if api_key is None:
            # Try environment variable, then default to test key
            self.api_key = os.getenv('OPENWEATHER_API_KEY', 'test-key')
        else:
            # Explicit value passed - validate it
            if not api_key or not api_key.strip():
                raise ValueError("OpenWeather API key is required")
            self.api_key = api_key.strip()
        
        # Handle bucket name validation  
        if bucket_name is None:
            # Try environment variable, then default
            self.bucket_name = os.getenv('WEATHER_CACHE_BUCKET', 'house-mgmt-weather-data')
        else:
            # Explicit value passed - validate it
            if not bucket_name or not bucket_name.strip():
                raise ValueError("S3 bucket name is required")
            self.bucket_name = bucket_name.strip()
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3', region_name='us-east-1')
        except Exception as e:
            log_error("Failed to initialize S3 client", error=str(e))
            self.s3_client = None
        
        # OpenWeather API configuration
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache_key = "current-weather.json"
        self.cache_expiry_hours = 1
        
        log_info(
            "Weather service initialized",
            bucket_name=self.bucket_name,
            has_s3_client=self.s3_client is not None
        )
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current weather and 5-day forecast with S3 caching
        
        Returns:
            Weather data dict with current conditions and 5-day forecast, or None if error
            
        Cache Strategy:
        1. Try to get from S3 cache
        2. If cache miss or expired, fetch from OpenWeather API
        3. Cache fresh data in S3
        4. Return weather data or None on error
        """
        try:
            log_info("Weather data request started")
            
            # Try to get from cache first
            cached_data = self._get_from_cache()
            if cached_data and self._is_cache_fresh(cached_data):
                log_info("Returning fresh cached weather data")
                return cached_data
            
            log_info("Cache miss or expired, fetching from OpenWeather API")
            
            # Fetch fresh data from API
            fresh_data = self._fetch_from_openweather_api()
            if fresh_data:
                # Cache the fresh data
                self._save_to_cache(fresh_data)
                log_info("Fresh weather data cached successfully")
                return fresh_data
            
            # API failed, try to return stale cached data if available
            if cached_data:
                log_info("API failed, returning stale cached data")
                return cached_data
            
            # No data available
            log_error("No weather data available (API failed and no cache)")
            return None
            
        except Exception as e:
            log_error("Failed to get weather data", error=str(e))
            return None
    
    def _get_from_cache(self) -> Optional[Dict[str, Any]]:
        """Get weather data from S3 cache"""
        if not self.s3_client:
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.cache_key
            )
            
            data = json.loads(response['Body'].read())
            log_info("Weather data retrieved from cache")
            return data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                log_info("No cached weather data found")
            else:
                log_error("Failed to retrieve from cache", error=str(e))
            return None
        except Exception as e:
            log_error("Error reading cached weather data", error=str(e))
            return None
    
    def _is_cache_fresh(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached data is still fresh (within expiry time)"""
        try:
            updated_at_str = cached_data.get('updated_at')
            if not updated_at_str:
                return False
            
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age = now - updated_at
            
            is_fresh = age.total_seconds() < (self.cache_expiry_hours * 3600)
            
            log_info(
                "Cache freshness check",
                age_minutes=age.total_seconds() / 60,
                is_fresh=is_fresh,
                expiry_hours=self.cache_expiry_hours
            )
            
            return is_fresh
            
        except Exception as e:
            log_error("Error checking cache freshness", error=str(e))
            return False
    
    def _fetch_from_openweather_api(self) -> Optional[Dict[str, Any]]:
        """Fetch fresh weather data from OpenWeather API"""
        try:
            # Fetch current weather
            current_url = f"{self.base_url}/weather"
            current_params = {
                'q': 'Willingboro,NJ,US',  # User location from requirements
                'appid': self.api_key,
                'units': 'imperial'  # Fahrenheit
            }
            
            current_response = requests.get(current_url, params=current_params, timeout=10)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Fetch 5-day forecast
            forecast_url = f"{self.base_url}/forecast"
            forecast_params = {
                'q': 'Willingboro,NJ,US',
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Transform to our standard format
            transformed_data = self._transform_weather_data(current_data, forecast_data)
            
            log_info("Weather data fetched successfully from OpenWeather API")
            return transformed_data
            
        except requests.RequestException as e:
            log_error("Failed to fetch from OpenWeather API", error=str(e))
            return None
        except Exception as e:
            log_error("Error processing OpenWeather API response", error=str(e))
            return None
    
    def _transform_weather_data(self, current_data: Dict, forecast_data: Dict) -> Dict[str, Any]:
        """Transform OpenWeather API response to our standard format"""
        try:
            now = datetime.now(timezone.utc)
            
            # Transform current weather
            current = {
                "temperature": round(current_data['main']['temp']),
                "humidity": current_data['main']['humidity'],
                "wind_speed": round(current_data['wind'].get('speed', 0)),
                "condition": current_data['weather'][0]['main'],
                "icon": current_data['weather'][0]['icon']
            }
            
            # Get today's high/low from forecast or current
            today_high = round(current_data['main'].get('temp_max', current_data['main']['temp']))
            today_low = round(current_data['main'].get('temp_min', current_data['main']['temp']))
            
            today = {
                "high": today_high,
                "low": today_low,
                "condition": current_data['weather'][0]['main'],
                "icon": current_data['weather'][0]['icon']
            }
            
            # Transform 5-day forecast
            forecast = self._process_forecast_data(forecast_data)
            
            result = {
                "current": current,
                "today": today,
                "forecast": forecast,
                "updated_at": now.isoformat()
            }
            
            log_info("Weather data transformed successfully")
            return result
            
        except Exception as e:
            log_error("Error transforming weather data", error=str(e))
            raise
    
    def _process_forecast_data(self, forecast_data: Dict) -> List[Dict[str, Any]]:
        """Process forecast data into 5-day summary"""
        try:
            forecast_list = forecast_data.get('list', [])
            if not forecast_list:
                return []
            
            # Group by date and get daily highs/lows
            daily_data = {}
            
            for item in forecast_list:
                dt_txt = item['dt_txt']  # Format: "2024-08-02 15:00:00"
                date_str = dt_txt.split(' ')[0]  # Get date part
                
                temp_max = item['main']['temp_max']
                temp_min = item['main']['temp_min']
                weather_info = item['weather'][0]
                
                if date_str not in daily_data:
                    daily_data[date_str] = {
                        'highs': [],
                        'lows': [],
                        'conditions': [],
                        'icons': []
                    }
                
                daily_data[date_str]['highs'].append(temp_max)
                daily_data[date_str]['lows'].append(temp_min)
                daily_data[date_str]['conditions'].append(weather_info['main'])
                daily_data[date_str]['icons'].append(weather_info['icon'])
            
            # Convert to 5-day forecast format
            forecast = []
            for date_str in sorted(daily_data.keys())[:5]:  # Limit to 5 days
                day_data = daily_data[date_str]
                
                # Get day name
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                
                # Get most common condition and icon
                most_common_condition = max(set(day_data['conditions']), key=day_data['conditions'].count)
                most_common_icon = max(set(day_data['icons']), key=day_data['icons'].count)
                
                forecast.append({
                    "day": day_name,
                    "high": round(max(day_data['highs'])),
                    "low": round(min(day_data['lows'])),
                    "icon": most_common_icon,
                    "condition": most_common_condition
                })
            
            return forecast
            
        except Exception as e:
            log_error("Error processing forecast data", error=str(e))
            return []
    
    def _save_to_cache(self, data: Dict[str, Any]) -> None:
        """Save weather data to S3 cache"""
        if not self.s3_client:
            return
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.cache_key,
                Body=json.dumps(data),
                ContentType='application/json'
            )
            
            log_info("Weather data cached successfully")
            
        except Exception as e:
            log_error("Failed to cache weather data", error=str(e))