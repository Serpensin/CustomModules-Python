import logging
import logging.handlers
import os
import threading
from collections import deque
from typing import Optional

from colorama import Fore, Style, init


class _BufferedTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    A TimedRotatingFileHandler that buffers log records in RAM during rotation.
    
    This prevents issues with concurrent writes during file rotation by temporarily
    storing incoming log records in a deque buffer while the rotation is in progress.
    """

    def __init__(self, *args, log_manager=None, **kwargs):
        """
        Initialize the buffered handler.
        
        Args:
            *args: Positional arguments passed to TimedRotatingFileHandler.
            log_manager (LogManager): Reference to the LogManager for accessing buffer state.
            **kwargs: Keyword arguments passed to TimedRotatingFileHandler.
        """
        super().__init__(*args, **kwargs)
        self.log_manager = log_manager

    def emit(self, record):
        """
        Emit a record, buffering it if rotation is in progress.
        
        Args:
            record (logging.LogRecord): The log record to emit.
        """
        if self.log_manager and self.log_manager.buffer_logs_during_rotation:
            # Check if rotation is in progress
            if self.log_manager._rotation_in_progress:
                # Buffer the record instead of writing it
                self.log_manager._log_buffer.append(record)
                return
        
        # Normal emit
        super().emit(record)

    def doRollover(self):
        """
        Perform a rollover, buffering incoming logs during the process.
        """
        if self.log_manager and self.log_manager.buffer_logs_during_rotation:
            # Signal that rotation is starting
            self.log_manager._rotation_in_progress = True
            
            try:
                # Perform the actual rotation
                super().doRollover()
            finally:
                # Signal that rotation is complete
                self.log_manager._rotation_in_progress = False
                
                # Flush buffered logs
                while self.log_manager._log_buffer:
                    buffered_record = self.log_manager._log_buffer.popleft()
                    super().emit(buffered_record)
        else:
            # No buffering, perform normal rotation
            super().doRollover()


class LogManager:
    """
    Manages the creation of loggers with both file and console handlers.

    Attributes:
        log_folder (str): The folder where log files will be stored.
        app_folder_name (str): The name of the application, used for naming the log file.
        log_level (int): The logging level (e.g., logging.INFO).
        logger (logging.Logger): Optional logger for meta-logging LogManager operations.
        buffer_logs_during_rotation (bool): If True, logs are buffered in RAM during rotation.
    """

    def __init__(
        self,
        log_folder,
        app_folder_name,
        log_level="INFO",
        logger: Optional[logging.Logger] = None,
        buffer_logs_during_rotation: bool = True,
    ):
        """
        Initializes the LogManager with the specified log folder, application folder name, and log level.

        Args:
            log_folder (str): The folder to store log files.
            app_folder_name (str): The name of the application.
            log_level (str): The log level as a string (e.g., 'INFO', 'DEBUG').
            logger (Optional[logging.Logger]): Parent logger for meta-logging LogManager operations.
            If provided, creates a child logger under CustomModules.LogHandler. Defaults to None.
            buffer_logs_during_rotation (bool): If True, incoming logs are buffered in RAM during
            file rotation to prevent issues. Defaults to True.
        """
        init()  # Initialize colorama for colored console output.

        # Setup meta-logger with child hierarchy: parent -> CustomModules -> LogHandler
        if logger:
            self.logger = logger.getChild("CustomModules").getChild("LogHandler")
        else:
            self.logger = logging.getLogger("CustomModules.LogHandler")

        self.logger.debug(
            f"Initializing LogManager for app '{app_folder_name}' in folder '{log_folder}'"
        )

        self.log_folder = log_folder
        self.app_folder_name = app_folder_name
        self.log_level = self._get_log_level(log_level)
        self._lock = threading.Lock()  # Thread-safety lock for handler operations
        self.buffer_logs_during_rotation = buffer_logs_during_rotation
        self._rotation_in_progress = False
        self._log_buffer = deque()  # Buffer for logs during rotation

        self.logger.info(f"LogManager initialized with log level {log_level}")

    def _get_log_level(self, log_level_str) -> int:
        """
        Converts a log level string to the corresponding logging level.

        Args:
            log_level_str (str): The log level as a string (e.g., 'INFO', 'DEBUG').

        Returns:
            int: The logging level.

        Raises:
            ValueError: If the log level string is invalid.
        """
        level = getattr(logging, log_level_str.upper(), None)
        if isinstance(level, int):
            return level
        else:
            raise ValueError(f"Invalid log level: {log_level_str}")

    def get_logger(self, logger_name) -> logging.Logger:
        """
        Creates and configures a logger with file and console handlers.

        Args:
            logger_name (str): The name of the logger.

        Returns:
            logging.Logger: The configured logger.
        """
        self.logger.debug(f"Creating logger: {logger_name}")

        # Create the logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(self.log_level)

        # Prevent duplicate handlers if logger already exists
        if logger.handlers:
            self.logger.debug(
                f"Logger {logger_name} already has handlers, returning existing logger"
            )
            return logger

        # Create a file handler that rotates logs at midnight with buffering support
        file_handler = _BufferedTimedRotatingFileHandler(
            filename=os.path.join(self.log_folder, f"{self.app_folder_name}.log"),
            when="midnight",
            encoding="utf-8",
            backupCount=27,
            delay=True,
            log_manager=self,
        )

        # Customize rotation naming: NAME.DATUM.log instead of NAME.log.DATUM
        file_handler.namer = lambda name: name.replace(".log", "") + ".log"

        # Make the file handler thread-safe by adding a lock
        original_emit = file_handler.emit

        def thread_safe_emit(record):
            with self._lock:
                original_emit(record)

        file_handler.emit = thread_safe_emit

        # Create a console handler with color support
        console_handler = logging.StreamHandler()

        # Create a formatter for the file handler
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        file_formatter = logging.Formatter(
            "[{asctime}] [PID:{process:<6}] [{levelname:<8}] {name}: {message}",
            dt_fmt,
            style="{",
        )
        file_handler.setFormatter(file_formatter)

        # Create a formatter for the console handler with color
        color_formatter = _ColoredFormatter(
            "[{asctime}] [PID:{process:<6}] [{levelname:<8}] {name}: {message}",
            dt_fmt,
            style="{",
        )
        console_handler.setFormatter(color_formatter)

        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger


class _ColoredFormatter(logging.Formatter):
    """
    A logging formatter that adds color to log messages based on their severity level.

    Attributes:
        COLOR_MAP (dict): A mapping of log levels to colorama color codes.
    """

    COLOR_MAP = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def format(self, record) -> str:
        """
        Formats the log record with color based on the log level.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message with color.
        """
        log_color = self.COLOR_MAP.get(record.levelname, Fore.WHITE)
        log_msg = super().format(record)
        return f"{log_color}{log_msg}{Style.RESET_ALL}"
