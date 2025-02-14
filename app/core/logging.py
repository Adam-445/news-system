import logging
import json
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler
from fastapi import Request
from pythonjsonlogger import json
import os

from app.middleware.correlation import correlation_id
from app.core.config import settings


class CustomJsonFormatter(json.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["correlation_id"] = (
            record.correlation_id if hasattr(record, "correlation_id") else None
        )
        log_record["level"] = record.levelname
        log_record["timestamp"] = self.formatTime(record)
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


def setup_logging():
    log_dir = "logs"
    # Create directory if it doesnt exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Choose formatter based on environment variable
    if settings.log_format == "json":
        formatter_config = {"()": CustomJsonFormatter}
    else:
        # Define a plain text formatter
        formatter_config = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {settings.log_format: formatter_config},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": settings.log_format,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": settings.log_format,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": settings.log_level,
        },
        "loggers": {
            "uvicorn.access": {"propagate": False},
            "uvicorn.error": {"propagate": False},
        },
    }
    dictConfig(logging_config)
