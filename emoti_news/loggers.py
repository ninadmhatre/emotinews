import logging
import os
from enum import StrEnum
from typing import Optional


# Define logger names
class LoggerNames(StrEnum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    JOBS = "jobs"

    def __iter__(self):
        return iter([self.FRONTEND, self.BACKEND, self.JOBS])


LOGGERS: dict[LoggerNames, logging.Logger] = {}


def _get_log_level(env_var: str, default: int) -> int:
    """Get log level from environment variable."""
    level_str = os.getenv(env_var, str(default))
    name_levels_map: dict[str, int] = logging.getLevelNamesMapping()

    return name_levels_map.get(level_str, default)


def _setup_loggers(default_level: int = logging.INFO):
    formatter = logging.Formatter("%(asctime)s %(name)s [%(levelname)s] %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    for logger_name in LoggerNames:
        logger = logging.getLogger(str(logger_name))
        logger.setLevel(_get_log_level("EMOTINEWS_LOG_LEVEL", default_level))
        logger.addHandler(console_handler)
        logger.propagate = False

        LOGGERS[logger_name] = logger


def set_log_level(level: str, logger_name: Optional[str | LoggerNames] = None):
    """
    Set log level for a specific logger or all loggers.

    Args:
        level: Log level as string ('DEBUG', 'INFO', etc.) or logging constant
        logger_name: Name of the logger to update. If None, updates all loggers
    """
    level_int = logging.getLevelNamesMapping()[level]
    logger_name = LoggerNames(logger_name) if logger_name else None

    if logger_name:
        if logger_name not in LOGGERS:
            raise ValueError(f"Unknown logger: {logger_name}. Available loggers: {list(LOGGERS.keys())}")

        _logger = LOGGERS[logger_name]
        _logger.setLevel(level_int)
        _logger.info(f"Log level set to {logging.getLevelName(level_int)}")
    else:
        # Update all loggers
        for name, logger in LOGGERS.items():
            logger.setLevel(level_int)
            logger.info(f"Log level for {name} set to {logging.getLevelName(level_int)}")


_setup_loggers()

frontend_logger = LOGGERS[LoggerNames.FRONTEND]
backend_logger = LOGGERS[LoggerNames.BACKEND]
jobs_logger = LOGGERS[LoggerNames.JOBS]
