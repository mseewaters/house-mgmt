"""
Weather API Routes
Following Best-practices.md: API → Service → DAL separation, structured logging, error handling
Following existing patterns from daily_task and other routes
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from house_mgmt.services.weather_service import WeatherService
from house_mgmt.utils.logging import log_info, log_error

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather")
async def get_weather(request: Request) -> Dict[str, Any]:
    """
    Get current weather conditions and 5-day forecast
    
    Returns:
        Weather data with current conditions, today's high/low, and 5-day forecast
        
    Raises:
        500: Internal server error
        503: Weather data unavailable
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        log_info(
            "weather_get_started",
            correlation_id=correlation_id
        )
        
        # Get weather data from service
        weather_service = WeatherService()
        weather_data = weather_service.get_current_weather()
        
        if weather_data is None:
            log_info(
                "weather_data_unavailable",
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=503,
                detail="Weather data is currently unavailable"
            )
        
        log_info(
            "weather_retrieved_successfully",
            correlation_id=correlation_id,
            temperature=weather_data.get("current", {}).get("temperature"),
            forecast_days=len(weather_data.get("forecast", []))
        )
        
        return weather_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log full details, return generic message (Best-practices.md requirement)
        log_error(
            "Failed to retrieve weather data",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving weather data"
        )