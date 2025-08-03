"""
Centralized logging utility for structured JSON logging
Enhanced with correlation ID context support
"""
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from contextvars import ContextVar

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)

# Context variable to store correlation ID for the current request
_correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)

def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())

def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for the current request context
    
    Args:
        correlation_id: Unique identifier for request tracing
    """
    _correlation_id.set(correlation_id)

def get_correlation_id() -> str:
    """
    Get correlation ID for the current request context
    
    Returns:
        Current correlation ID or None if not set
    """
    return _correlation_id.get()

def _create_log_entry(level: str, message: str, **kwargs) -> Dict[str, Any]:
    """
    Create a structured log entry with correlation ID
    Enhanced to automatically include correlation ID when available
    """
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        **kwargs
    }
    
    # Add correlation ID if available and not already in kwargs
    correlation_id = get_correlation_id()
    if correlation_id and 'correlation_id' not in kwargs:
        log_data["correlation_id"] = correlation_id
    
    return log_data

def log_info(message: str, **kwargs):
    """Log info level message with structured data"""
    log_data = _create_log_entry("INFO", message, **kwargs)
    logger.info(json.dumps(log_data))

def log_debug(message: str, **kwargs):
    """Log debug level message with structured data (only if debug enabled)"""
    if logger.isEnabledFor(logging.DEBUG):
        log_data = _create_log_entry("DEBUG", message, **kwargs)
        logger.debug(json.dumps(log_data))

def log_error(message: str, **kwargs):
    """Log error level message with structured data"""
    log_data = _create_log_entry("ERROR", message, **kwargs)
    logger.error(json.dumps(log_data))

def log_warning(message: str, **kwargs):
    """Log warning level message with structured data"""
    log_data = _create_log_entry("WARNING", message, **kwargs)
    logger.warning(json.dumps(log_data))