from functools import lru_cache
from typing import List, Dict

from fastapi import Depends
from sqlmodel import Session

from API import database, crud, config


def _get_db_session(session: Session = Depends(database.get_session)):
    return session


@lru_cache(maxsize=1)
def get_cached_item_ids(session: Session = Depends(_get_db_session)) -> List[str]:
    return crud.get_all_items_info(session)


@lru_cache
def get_debug_settings() -> config.DebugSettings:
    """
    Return the cached settings instance. This ensures the Settings object is only created once,
    and reused across requests, improving performance.
    """
    return config.DebugSettings()


@lru_cache
def get_database_config() -> config.DatabaseConfig:
    """
    Return the cached DatabaseConfig instance. This ensures the Settings object is only created once,
    and reused across requests, improving performance.
    """
    return config.DatabaseConfig()