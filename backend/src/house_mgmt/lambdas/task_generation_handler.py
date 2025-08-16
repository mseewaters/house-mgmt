"""
Task Generation Lambda Handler - Scheduled daily task generation from recurring templates
Following Best-practices.md: Lambda handlers, structured logging, error handling, UTC timestamps
Triggered by EventBridge at midnight local time to generate tomorrow's tasks
"""
import json
import os
import pytz
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any
from services.daily_task_generation_service import DailyTaskGenerationService
from utils.logging import log_info, log_error


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for scheduled daily task generation
    
    Triggered by: EventBridge scheduled rule (daily at midnight local time)
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context object
        
    Returns:
        Dict with statusCode, body containing generation results
        
    Process:
        1. Get target date
        2. Generate daily tasks from active recurring templates
        3. Log execution details and performance metrics
        4. Return success/error response
    """
    request_id = getattr(context, 'aws_request_id', 'unknown')
    start_time = datetime.now(timezone.utc)
    
    try:
        log_info(
            "task_generation_lambda_started",
            request_id=request_id,
            event_source=event.get('source'),
            trigger_time=start_time.isoformat(),
            cron_explanation="1 AM EST (6 AM UTC) generates tasks for current local day"
        )
        
        # Get target date for task generation
        target_date = get_target_date()
        
        log_info(
            "task_generation_target_date_determined",
            target_date=target_date,
            request_id=request_id,
            note="Generating tasks for kitchen local date"
        )
        
        # Initialize task generation service
        table_name = os.getenv('DYNAMODB_TABLE')
        if not table_name:
            raise ValueError("DYNAMODB_TABLE environment variable not set")
        
        try:
            generation_service = DailyTaskGenerationService(table_name=table_name)
            
            # Generate daily tasks for tomorrow
            generated_tasks = generation_service.generate_daily_tasks_for_date(target_date)
            
        except Exception as service_error:
            # Handle service-level errors (database connection, etc.)
            log_error(
                "task_generation_service_error",
                error=str(service_error),
                error_type=type(service_error).__name__,
                request_id=request_id,
                target_date=target_date
            )
            # Re-raise to be caught by outer exception handler
            raise RuntimeError(f"Task generation service failed: {str(service_error)}")
        
        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Determine success message
        if len(generated_tasks) == 0:
            message = f"No recurring tasks found for task generation on {target_date}"
        else:
            message = f"Successfully generated {len(generated_tasks)} daily tasks for {target_date}"
        
        log_info(
            "task_generation_lambda_completed",
            request_id=request_id,
            target_date=target_date,
            generated_count=len(generated_tasks),
            execution_time_ms=execution_time_ms,
            success=True
        )
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'target_date': target_date,
                'generated_count': len(generated_tasks),
                'message': message,
                'execution_time_ms': execution_time_ms,
                'request_id': request_id
            })
        }
        
    except ValueError as e:
        # Configuration or validation errors
        execution_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        log_error(
            "task_generation_lambda_validation_error",
            error=str(e),
            request_id=request_id,
            execution_time_ms=execution_time_ms
        )
        
        return {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': f"Configuration error: {str(e)}",
                'request_id': request_id,
                'execution_time_ms': execution_time_ms
            })
        }
        
    except Exception as e:
        # Unexpected errors
        execution_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        log_error(
            "task_generation_lambda_unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
            request_id=request_id,
            execution_time_ms=execution_time_ms
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': "An error occurred during task generation",
                'request_id': request_id,
                'execution_time_ms': execution_time_ms
            })
        }


def get_target_date() -> str:
    """
    Get target date in local timezone (EST/EDT) in YYYY-MM-DD format
    
    Returns:
        Target date as ISO format string (YYYY-MM-DD) in local timezone
        
    Note:
        Kitchen tablet is in EST/EDT. Lambda runs at 1 AM EST (6 AM UTC)
        to generate tasks for the current local day (which is "tomorrow" in UTC).
    """
    try:
        # Define kitchen timezone (handles EST/EDT automatically)
        kitchen_tz = pytz.timezone('America/New_York')
        
        # Get current time in kitchen timezone
        kitchen_now = datetime.now(kitchen_tz)
        
        # Get today's date in kitchen timezone
        # At 1 AM EST, we want tasks for TODAY (not tomorrow)
        kitchen_today = kitchen_now.date()
        
        log_info(
            "calculated_target_date",
            utc_now=datetime.now(timezone.utc).isoformat(),
            kitchen_now=kitchen_now.isoformat(),
            kitchen_today=kitchen_today.isoformat(),
            kitchen_timezone=str(kitchen_tz)
        )
        
        return kitchen_today.isoformat()
        
    except Exception as e:
        log_error("Failed to calculate target date", error=str(e))
        # Fallback: Use UTC date
        utc_now = datetime.now(timezone.utc)
        return utc_now.date().isoformat()
