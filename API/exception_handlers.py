import logging
import traceback
import uuid
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from API import config, dependencies


def log_traceback_to_file(traceback_info: str, exc_id: str, log_file_path: Path):
    """
    Log the full traceback to a separate log file with a unique exception ID.
    """
    with open(log_file_path, "a") as f:
        f.write(f"Exception ID: {exc_id}\n")
        f.write(traceback_info)
        f.write("\n\n")


def handle_http_exception(exc: HTTPException, request: Request, settings: BaseSettings, log_file_path: Path):
    """
    Handles HTTP exceptions globally and logs them.
    """
    exc_id = str(uuid.uuid4())  # Generate a unique ID for the exception
    logging.error(f"HTTPException [{exc_id}]: {exc.detail} - Path: {request.url.path}")

    if settings.DEBUG:
        traceback_info = traceback.format_exc()
        log_traceback_to_file(traceback_info, exc_id, log_file_path)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "exception_id": exc_id,
            "debug_info": traceback_info if settings.DEBUG else None,
        }
    )


def handle_validation_exception(exc: ValidationError, request: Request, settings: BaseSettings, log_file_path: Path):
    """
    Handles Pydantic ValidationErrors and logs them.
    """
    exc_id = str(uuid.uuid4())  # Generate a unique ID for the exception
    logging.error(f"ValidationError [{exc_id}]: {exc.errors()} - Path: {request.url.path}")

    if settings.DEBUG:
        traceback_info = traceback.format_exc()
        log_traceback_to_file(traceback_info, exc_id, log_file_path)

    return JSONResponse(
        status_code=422,  # Unprocessable Entity
        content={
            "detail": "Validation error occurred.",
            "errors": exc.errors(),
            "exception_id": exc_id,
            "debug_info": traceback_info if settings.DEBUG else None,
        }
    )


def handle_generic_exception(exc: Exception, request: Request, settings: BaseSettings, log_file_path: Path):
    """
    Handles generic exceptions (500 errors) and logs them.
    """
    exc_id = str(uuid.uuid4())  # Generate a unique ID for the exception
    logging.error(f"Unhandled Exception [{exc_id}]: {str(exc)} - Path: {request.url.path}")

    if settings.DEBUG:
        traceback_info = traceback.format_exc()
        log_traceback_to_file(traceback_info, exc_id, log_file_path)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "exception_id": exc_id,
            "debug_info": traceback_info if settings.DEBUG else None,
        }
    )


def handle_exception(request: Request, exc: Exception):
    """
    Custom exception handler that logs a short error message to app.log and docker logs,
    writes the full traceback to a separate file in the tracebacks folder,
    and returns a JSON response depending on the DEBUG flag in settings.
    """
    settings = dependencies.get_debug_settings()
    logger = logging.getLogger("uvicorn.error")
    traceback_dir = Path("logs/tracebacks")
    traceback_dir.mkdir(exist_ok=True)

    # Generate a unique filename for the traceback log
    traceback_filename = traceback_dir / f"traceback_{uuid.uuid4()}.log"

    # Determine if we are in DEBUG mode
    debug_mode = settings.DEBUG

    # Write the full traceback to a separate file
    with traceback_filename.open("w") as f:
        f.write(f"Traceback (most recent call last):\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))

    # Log a short error message to the app.log and docker logs
    logger.error(f"An error occurred at {request.url}: {str(exc)} - See traceback in {traceback_filename}")
    # Manage the number of files in the traceback folder
    manage_traceback_files(traceback_dir, settings)
    # JSON response
    if isinstance(exc, HTTPException):
        # If it's an HTTPException, use its status_code and detail
        status_code = exc.status_code
        detail = exc.detail
    else:
        # For any other exception, return a generic 500 error response
        status_code = 500
        detail = "Internal Server Error"

    if debug_mode:
        # Return the full traceback in the response if DEBUG mode is enabled
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__)
            }
        )
    else:
        # Return only the short error message
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail}
        )


def manage_traceback_files(traceback_dir: Path, settings):
    """
    Ensures the number of traceback files in the directory does not exceed the limit.
    Deletes the oldest files if the limit is exceeded.
    """
    files = list(traceback_dir.glob("traceback_*.log"))

    # Sort the files by creation time (oldest first)
    files.sort(key=lambda f: f.stat().st_ctime)

    # Remove oldest files if we exceed the limit
    if len(files) > settings.MAX_TRACEBACK_FILES:
        for file_to_delete in files[:len(files) - settings.MAX_TRACEBACK_FILES]:
            try:
                file_to_delete.unlink()  # Deletes the file
            except OSError as e:
                logging.error(f"Error deleting old traceback file {file_to_delete}: {e}")
