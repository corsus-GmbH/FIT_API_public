from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class DebugSettings(BaseSettings):
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    MAX_TRACEBACK_FILES: int = 100
    SHOW_ACCESS_LOGS:bool = True

    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / "config" / "debug.env")

class DatabaseConfig(BaseSettings):
    # Database configuration with default values
    DATABASE_URL: str = f"sqlite:///{(Path(__file__).parent.parent / 'data' / 'FIT.db').resolve()}"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_TIMEOUT: int = 30
    ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / "config" / "database.env",
        env_file_encoding="utf-8",
    )