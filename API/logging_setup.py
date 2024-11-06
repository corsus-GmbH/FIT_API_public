# logging_setup.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import asyncio
from typing import Optional

from uvicorn.logging import AccessFormatter
from API import dependencies
from API import exceptions


def setup_logging() -> None:
    """
    Setup logging for the application.

    This function initializes log directories, configures loggers and their handlers,
    and manages error logging centrally without interrupting the startup process.
    """
    # Initialize the main uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.DEBUG)
    # Create log directories
    log_directory = Path("logs")
    traceback_directory = log_directory / "tracebacks"
    try:
        log_directory.mkdir(parents=True, exist_ok=True)
        traceback_directory.mkdir(parents=True, exist_ok=True)
        uvicorn_logger.debug(f"Log directories ensured at: {log_directory}, {traceback_directory}")
    except Exception as directory_creation_error:
        # Log the warning if directories cannot be created
        uvicorn_logger.warning(f"Failed to create log directories: {directory_creation_error}")

    # Define log files
    application_log_file = log_directory / "app.log"
    access_log_file = log_directory / "access.log"
    sqlalchemy_log_file = log_directory / "sql.log"

    # Define formatters
    general_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Retrieve settings
    application_settings = dependencies.get_debug_settings()

    # Retrieve desired log level from settings
    desired_log_level_name = application_settings.LOG_LEVEL.upper()
    desired_log_level = getattr(logging, desired_log_level_name, logging.INFO)
    initial_sql_log_level = logging.INFO

    # Configure loggers and handlers
    try:
        configure_uvicorn_logger(application_log_file, general_formatter, desired_log_level)
        uvicorn_logger.debug("Uvicorn logger configured successfully.")
    except exceptions.LoggingSetupError as uvicorn_error:
        uvicorn_logger.warning(f"Failed to setup uvicorn logger: {uvicorn_error}")

    try:
        configure_uvicorn_access_logger(
            access_log_file, desired_log_level, application_settings.SHOW_ACCESS_LOGS
        )
        uvicorn_logger.debug("Uvicorn access logger configured successfully.")
    except exceptions.LoggingSetupError as access_error:
        uvicorn_logger.warning(f"Failed to setup uvicorn.access logger: {access_error}")

    try:
        configure_sqlalchemy_logger(sqlalchemy_log_file, general_formatter, initial_sql_log_level)
        uvicorn_logger.debug("SQLAlchemy logger configured successfully.")
    except exceptions.LoggingSetupError as sqlalchemy_error:
        uvicorn_logger.warning(f"Failed to setup SQLAlchemy logger: {sqlalchemy_error}")

    # Log initial setup completion
    try:
        uvicorn_logger.info("Initial logging setup complete.")
    except Exception as initial_log_error:
        uvicorn_logger.warning(f"Failed to log initial setup message: {initial_log_error}")


def configure_uvicorn_logger(
        application_log_file: Path,
        formatter: logging.Formatter,
        desired_log_level: int
) -> None:
    """
    Configure the uvicorn logger and attach the app.log file handler.

    Args:
        application_log_file (Path): Path to the app.log file.
        formatter (logging.Formatter): Formatter for the file handler.
        desired_log_level (int): Desired logging level.

    Raises:
        exceptions.LoggingSetupError: If setting log level or configuring handler fails.
    """
    uvicorn_logger = logging.getLogger("uvicorn")
    # Determine initial log level
    initial_log_level = desired_log_level if desired_log_level < logging.INFO else logging.INFO

    # Set initial log level for the uvicorn logger
    uvicorn_logger.setLevel(initial_log_level)

    # Create file handler for app.log
    try:
        application_file_handler = RotatingFileHandler(
            application_log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        application_file_handler.setFormatter(formatter)
        application_file_handler.setLevel(initial_log_level)

        # Add handler to uvicorn logger
        uvicorn_logger.addHandler(application_file_handler)

        # Verify that the handler has been added
        if application_file_handler not in uvicorn_logger.handlers:
            raise exceptions.LoggingSetupError("app.log file handler was not added to uvicorn logger.")

    except Exception as handler_error:
        raise exceptions.LoggingSetupError(f"Error setting up app.log handler: {handler_error}")


def get_app_file_handler(logger: logging.Logger) -> RotatingFileHandler:
    """
    Retrieve the app.log file handler from the given logger.

    Args:
        logger (logging.Logger): The logger to search for the app.log handler.

    Returns:
        RotatingFileHandler: The app.log file handler.

    Raises:
        exceptions.LoggingSetupError: If the app.log handler is not found.
    """
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            if Path(handler.baseFilename).name == 'app.log':
                return handler
    raise exceptions.LoggingSetupError("app.log file handler not found.")


def configure_uvicorn_access_logger(
        access_log_file: Path,
        desired_log_level: int,
        show_access_logs: bool
) -> None:
    """
    Configure the uvicorn.access logger and attach the access.log file handler.

    Args:
        access_log_file (Path): Path to the access.log file.
        desired_log_level (int): Desired logging level.
        show_access_logs (bool): Whether to show access logs on the console.

    Raises:
        exceptions.LoggingSetupError: If setting log level or configuring handler fails.
    """
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(desired_log_level)

    # Create file handler for access.log using AccessFormatter
    try:
        access_file_handler = RotatingFileHandler(
            access_log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        access_formatter = AccessFormatter()
        access_file_handler.setFormatter(access_formatter)
        access_file_handler.setLevel(desired_log_level)
        uvicorn_access_logger.addHandler(access_file_handler)

        # Verify that the handler has been added
        if access_file_handler not in uvicorn_access_logger.handlers:
            raise exceptions.LoggingSetupError("access.log file handler was not added to uvicorn.access logger.")

    except Exception as handler_error:
        raise exceptions.LoggingSetupError(f"Error setting up access.log handler: {handler_error}")

    # Optionally, add or remove console handlers based on SHOW_ACCESS_LOGS
    if not show_access_logs:
        try:
            # Remove all StreamHandlers to prevent access logs from appearing in the console
            for handler in uvicorn_access_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler):
                    uvicorn_access_logger.removeHandler(handler)
            uvicorn_access_logger.addHandler(access_file_handler)
        except Exception as handler_removal_error:
            raise exceptions.LoggingSetupError(
                f"Error removing console handlers from uvicorn.access logger: {handler_removal_error}")


def configure_sqlalchemy_logger(
        sqlalchemy_log_file: Path,
        formatter: logging.Formatter,
        desired_log_level: int
) -> None:
    """
    Configure the SQLAlchemy logger and attach the sql.log file handler.

    Args:
        sqlalchemy_log_file (Path): Path to the sql.log file.
        formatter (logging.Formatter): Formatter for the file handler.
        desired_log_level (int): Desired logging level.

    Raises:
        exceptions.LoggingSetupError: If setting log level or configuring handler fails.
    """
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(desired_log_level)

    # Create file handler for sql.log
    try:
        sqlalchemy_file_handler = RotatingFileHandler(
            sqlalchemy_log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        sqlalchemy_file_handler.setFormatter(formatter)
        sqlalchemy_file_handler.setLevel(desired_log_level)
        sqlalchemy_logger.addHandler(sqlalchemy_file_handler)

        # Verify that the handler has been added
        if sqlalchemy_file_handler not in sqlalchemy_logger.handlers:
            raise exceptions.LoggingSetupError("sql.log file handler was not added to sqlalchemy.engine logger.")

    except Exception as handler_error:
        raise exceptions.LoggingSetupError(f"Error setting up sql.log handler: {handler_error}")

    # Remove console handlers to prevent SQL logs from appearing in the console
    try:
        for handler in sqlalchemy_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                sqlalchemy_logger.removeHandler(handler)
        sqlalchemy_logger.addHandler(sqlalchemy_file_handler)
    except Exception as handler_removal_error:
        raise exceptions.LoggingSetupError(
            f"Error removing console handlers from sqlalchemy.engine logger: {handler_removal_error}")


def needs_log_level_adjustment() -> Optional[RotatingFileHandler]:
    """
    Determine whether the log levels need adjustment.

    Returns:
        Optional[RotatingFileHandler]: The app.log file handler if adjustment is needed, else None.
    """
    # Retrieve the desired log level from settings
    settings = dependencies.get_debug_settings()
    desired_log_level_name = settings.LOG_LEVEL.upper()
    desired_log_level = getattr(logging, desired_log_level_name, logging.INFO)

    # Retrieve the uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    current_uvicorn_level = uvicorn_logger.getEffectiveLevel()

    try:
        app_file_handler = get_app_file_handler(uvicorn_logger)
    except exceptions.LoggingSetupError as logging_setup_error:
        uvicorn_logger.warning(f"Logging setup error: {logging_setup_error}")
        return None  # Cannot adjust without the handler

    current_app_handler_level = app_file_handler.level

    # Log the current and desired log levels for debugging
    uvicorn_logger.info(
        f"Checking log levels: uvicorn_logger={logging.getLevelName(current_uvicorn_level)}, "
        f"app_file_handler={logging.getLevelName(current_app_handler_level)}, "
        f"desired={logging.getLevelName(desired_log_level)}"
    )

    # Check if either log level differs from the desired level
    if current_uvicorn_level != desired_log_level or current_app_handler_level != desired_log_level:
        uvicorn_logger.debug("Log levels differ. Adjustment needed.")
        return app_file_handler
    else:
        uvicorn_logger.debug("Log levels already match desired settings. No adjustment needed.")
        return None


async def adjust_log_level(app_file_handler: RotatingFileHandler, delay_seconds: int = 2) -> None:
    """
    Adjust the log levels of the uvicorn logger and the app.log handler after a delay.

    Args:
        app_file_handler (RotatingFileHandler): The app.log file handler to adjust.
        delay_seconds (int, optional): Delay before adjusting the log level. Defaults to 2 seconds.
    """
    await asyncio.sleep(delay_seconds)  # Delay to ensure startup logs are captured

    # Retrieve the uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")

    # Retrieve desired log level from settings
    application_settings = dependencies.get_debug_settings()
    desired_log_level_name = application_settings.LOG_LEVEL.upper()

    # Validate and map the log level name to its corresponding logging level
    if hasattr(logging, desired_log_level_name):
        desired_log_level = getattr(logging, desired_log_level_name)
    else:
        uvicorn_logger.warning(f"Invalid LOG_LEVEL '{desired_log_level_name}'. Defaulting to 'INFO'.")
        desired_log_level = logging.INFO

    # Log the desired log level for debugging purposes
    uvicorn_logger.debug(
        f"Desired log level retrieved from settings: {desired_log_level_name} ({desired_log_level})"
    )

    try:
        # Adjust the uvicorn logger's level
        uvicorn_logger.setLevel(desired_log_level)
        uvicorn_logger.info(f"Uvicorn logger level set to {logging.getLevelName(desired_log_level)}.")

        # Adjust the app.log file handler's level
        app_file_handler.setLevel(desired_log_level)
        uvicorn_logger.info(f"app.log handler level set to {logging.getLevelName(desired_log_level)}.")
    except exceptions.LoggingSetupError as logging_setup_error:
        # Log the LoggingSetupError as a warning
        uvicorn_logger.warning(f"Logging setup error during log level adjustment: {logging_setup_error}")
    except Exception as unexpected_error:
        # Log any other unexpected errors as warnings
        uvicorn_logger.warning(
            f"Failed to adjust log level due to an unexpected error: {unexpected_error}. Keeping existing log level."
        )


def adjust_sql_log_level() -> None:
    """
    Adjusts the SQLAlchemy logger to the desired log level after database setup.
    Handles any setup errors gracefully.
    """
    # Retrieve settings
    logger = logging.getLogger("uvicorn")
    application_settings = dependencies.get_debug_settings()
    desired_log_level_name = application_settings.LOG_LEVEL.upper()
    desired_log_level = getattr(logging, desired_log_level_name, logging.INFO)

    # Adjust SQLAlchemy logger's level with proper error handling
    try:
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(desired_log_level)
        logger.info(f"SQLAlchemy logger level set to {logging.getLevelName(desired_log_level)}.")
    except exceptions.LoggingSetupError as logging_setup_error:
        # Log the LoggingSetupError as a warning
        logger.warning(f"Logging setup error during SQLAlchemy log level adjustment: {logging_setup_error}")
    except Exception as unexpected_error:
        # Log any other unexpected errors as warnings
        logger.warning(
            f"Failed to adjust SQLAlchemy log level due to an unexpected error: {unexpected_error}. Keeping existing log level."
        )


if __name__ == "__main__":
    print("This is only a library. Nothing will happen when you execute it.")
