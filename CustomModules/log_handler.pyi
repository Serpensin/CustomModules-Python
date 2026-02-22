"""Type stubs for log_handler module."""
import logging
from typing import Optional

class LogManager:
    logger: logging.Logger
    def __init__(
        self,
        bot_name: str,
        log_level: str = "INFO",
        log_folder: str = "logs",
        log_to_console: bool = True,
        log_to_file: bool = True,
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        console_log_format: Optional[str] = None,
        file_log_format: Optional[str] = None,
        log_retention_days: int = 7,
        log_rotation_when: str = "midnight",
        log_rotation_interval: int = 1,
        buffer_logs_during_rotation: bool = True,
    ) -> None: ...
    def get_logger(self) -> logging.Logger: ...
    def set_level(self, level: str) -> None: ...
