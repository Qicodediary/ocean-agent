"""
Structured Logging Configuration
Converts all logs to JSON format for production observability
"""

import json
import logging
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Simple JSON formatter without conflicting fields"""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add any extra fields (but not conflicting ones)
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                # Skip internal logging fields
                if key not in ('name', 'msg', 'args', 'created', 'filename', 'funcName', 
                               'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                               'message', 'pathname', 'process', 'processName', 'relativeCreated',
                               'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                               'asctime'):
                    log_obj[key] = value
        
        return json.dumps(log_obj)


def setup_logging(name="ocean_model"):
    """Configure structured JSON logging"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    json_formatter = JSONFormatter()
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logging()
