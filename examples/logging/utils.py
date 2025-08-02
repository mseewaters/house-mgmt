# Centralized logging utility
import logging
import json
from datetime import datetime, timezone

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def log_info(message: str, **kwargs):
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "message": message,
        **kwargs
    }
    logging.info(json.dumps(log_data))

def log_debug(message: str, **kwargs):
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "DEBUG",
            "message": message,
            **kwargs
        }
        logging.debug(json.dumps(log_data))

def log_error(message: str, **kwargs):
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "message": message,
        **kwargs
    }
    logging.error(json.dumps(log_data))