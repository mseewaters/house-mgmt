"""
Centralized logging utility for structured JSON logging
"""
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)

def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())

def _create_log_entry(level: str, message: str, **kwargs) -> Dict[str, Any]:
    """Create a structured log entry"""
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        **kwargs
    }
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