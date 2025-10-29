"""Type stubs for LogHandler module."""
import logging
from typing import Optional

class LogManager:
    """Manages the creation of loggers with both file and console handlers."""
    
    log_folder: str
    app_folder_name: str
    log_level: int
    
    def __init__(
        self,
        log_folder: str,
        app_folder_name: str,
        log_level: str = "INFO"
    ) -> None: ...
    
    def get_logger(
        self,
        logger_name: str,
        max_file_size: int = 10485760,
        backup_count: int = 5
    ) -> logging.Logger: ...

__all__ = ['LogManager']
