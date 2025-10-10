import logging
import sys
import os
import shutil
from pathlib import Path
from typing import Optional

# Global flag to track if advanced logging has been initialized
_advanced_logging_initialized = False

def clear_logs_directory(logs_dir: str = "tmp_logs") -> None:
    """
    Clear all log files from previous runs.
    
    Args:
        logs_dir: Directory containing log files
    """
    logs_path = Path(logs_dir)
    if logs_path.exists():
        shutil.rmtree(logs_path)
    logs_path.mkdir(exist_ok=True)

def setup_advanced_logging(console_level: str = "INFO", logs_dir: str = "tmp_logs") -> None:
    """
    Set up advanced multi-file logging system.
    
    Args:
        console_level: Logging level for console output
        logs_dir: Directory to store log files
    """
    global _advanced_logging_initialized
    
    if _advanced_logging_initialized:
        return
    
    # Clear and create logs directory
    clear_logs_directory(logs_dir)
    
    # Get root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.DEBUG)  # Capture everything at root level
    
    # Create detailed formatter for files
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create simple formatter for console
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # Console handler with specified level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # DEBUG file handler (everything)
    debug_handler = logging.FileHandler(f'{logs_dir}/DEBUG.log')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(file_formatter)
    root_logger.addHandler(debug_handler)
    
    # INFO file handler (INFO and above)
    info_handler = logging.FileHandler(f'{logs_dir}/INFO.log')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(file_formatter)
    root_logger.addHandler(info_handler)
    
    # WARNING file handler (WARNING and above)
    warning_handler = logging.FileHandler(f'{logs_dir}/WARNING.log')
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(file_formatter)
    root_logger.addHandler(warning_handler)
    
    # ERROR file handler (ERROR and above)
    error_handler = logging.FileHandler(f'{logs_dir}/ERROR.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    _advanced_logging_initialized = True

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting and configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to also log to file
        format_string: Optional custom format string
    
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a logger instance. If advanced logging is initialized, 
    just return a logger that uses the global configuration.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (only used if advanced logging not initialized)
    
    Returns:
        Logger instance
    """
    if _advanced_logging_initialized:
        # Return logger that uses the global advanced configuration
        return logging.getLogger(name)
    else:
        # Fallback to simple logger setup
        return setup_logger(name, level)