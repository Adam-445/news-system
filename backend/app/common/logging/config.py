import logging
import os
from datetime import datetime, timezone
from logging.config import dictConfig

from pythonjsonlogger import jsonlogger

from backend.app.common.config.settings import settings
from backend.app.common.middleware.correlation import correlation_id


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def formatTime(self, record, datefmt=None):
        # Convert the created timestamp to a timezone-aware datetime (UTC)
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add correlation ID
        log_record["correlation_id"] = correlation_id.get() or ""

        # Standard fields
        log_record.update(
            {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "process": record.process,
                "thread": record.threadName,
            }
        )


def setup_logging():
    log_dir = "logs"

    log_format = settings.log_format.lower()
    log_level = settings.log_level.upper()

    # Define the console handler (always used)
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if log_format == "json" else "simple",
            "stream": "ext://sys.stdout",
        },
    }

    if settings.environment != "production":
        # Ensure the directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Add file handler for non-production environments
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(log_dir, "backend.app.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json" if log_format == "json" else "simple",
            "encoding": "utf8",
        }

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": CustomJsonFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S %z",
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S %z",
            },
        },
        "handlers": handlers,
        "loggers": {
            "app": {
                "handlers": list(handlers.keys()),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": list(handlers.keys()),
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": list(handlers.keys()),
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": list(handlers.keys()),
                "level": "WARNING",
                "propagate": False,
            },
        },
        "root": {
            "handlers": list(handlers.keys()),
            "level": log_level,
        },
    }

    dictConfig(LOGGING_CONFIG)


# Initialize logging when the module is imported.
setup_logging()
logger = logging.getLogger("app")
