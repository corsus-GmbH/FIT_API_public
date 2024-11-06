# database.py

"""
This module provides the database configuration and utility functions.
It includes functions to create the database and tables individually,
and to get a session.
"""
import logging

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import inspect
from typing import Type

from API import config
from API import models

logger = logging.getLogger('uvicorn')


def get_engine():
    try:
        # Directly instantiate the DatabaseConfig class
        config_instance = config.DatabaseConfig()
        engine = create_engine(
            config_instance.DATABASE_URL,
            pool_size=config_instance.POOL_SIZE,
            max_overflow=config_instance.MAX_OVERFLOW,
            pool_timeout=config_instance.POOL_TIMEOUT,
            echo=config_instance.ECHO,
        )
        return engine
    except Exception as unexpected_error:
        raise ConnectionError(
            f"Unexpected error when creating engine: {unexpected_error}"
        ) from unexpected_error


def create_tables() -> None:
    """
    Create all database tables at once and then verify that they exist and are not empty.

    Raises:
        RuntimeError: If any table fails to be created or is empty after creation.
    """
    engine = get_engine()
    model_registry = models.ModelRegistry()

    try:
        # Create all tables at once
        SQLModel.metadata.create_all(engine)

        # Use a single session for all checks
        with Session(engine) as session:
            for table_name, model_class in model_registry._registry.items():
                # Verify if the table exists
                if not table_exists(engine, model_class):
                    raise RuntimeError(f"Table '{model_class.__tablename__}' was not created.")

                # Check if the table is empty
                records = session.exec(select(model_class)).all()
                if not records:
                    raise RuntimeError(f"Table '{model_class.__tablename__}' is empty.")
    except Exception as unexpected_error:
        raise RuntimeError(
            f"An error occurred during table creation: {unexpected_error}"
        ) from unexpected_error


def table_exists(engine, model_class: Type[SQLModel]) -> bool:
    """
    Check if a table exists in the database.

    Args:
        engine: The database engine.
        model_class: The SQLModel class representing the table.

    Returns:
        True if the table exists, False otherwise.
    """
    inspector = inspect(engine)
    return inspector.has_table(model_class.__tablename__)


def get_session() -> Session:
    engine = get_engine()
    try:
        with Session(engine) as session:
            yield session
    except Exception as unexpected_error:
        raise RuntimeError(
            f"An unexpected error occurred while obtaining session: {unexpected_error}"
        ) from unexpected_error


if __name__ == "__main__":
    print("This is only a library. Nothing will happen when you execute it.")
