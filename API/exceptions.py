import logging
import traceback
from typing import Union
from fastapi import HTTPException
from pydantic import ValidationError as PydanticValidationError


ValidationError = PydanticValidationError
class LoggingSetupError(Exception):
    """
    Custom exception raised when logging setup fails.
    """

    def __init__(self, message: str):
        super().__init__(message)

class ValueError(Exception):
    pass

class UnknownError(Exception):
    """Raised when an unknown or unexpected error occurs."""

    def __init__(self, message: str = "An unknown error occurred"):
        super().__init__(message)


class MinMaxValueNotFoundError(Exception):
    """Raised when the minimum or maximum value is not found for a specified category or stage."""

    def __init__(self, category: str, identifier: str, scheme_id: str):
        message = f"Min or Max value not found for {category} with ID '{identifier}' under scheme ID '{scheme_id}'."
        super().__init__(message)


class InvalidItemCountryAcronymFormatError(HTTPException):
    """Raised when the item_id-country_acronym format is invalid."""

    def __init__(self, raw_string: str):
        detail = f"Invalid format for item_id-country_acronym: '{raw_string}'. Expected format: 'item_id-country_acronym'."
        super().__init__(status_code=422, detail=detail)


class ImpactCategoryNotFoundError(Exception):
    """Exception raised when an ImpactCategory with a given ic_id is not found."""
    pass


class WeightingSchemeNameNotFoundError(HTTPException):
    """Raised when the weighting scheme name is not found in the database."""

    def __init__(self, scheme_id: int):
        detail = f"Weighting scheme name not found for the provided scheme ID: {scheme_id}."
        super().__init__(status_code=404, detail=detail)


class WeightingSchemeIDNotFoundError(HTTPException):
    """Raised when the weighting scheme ID is not found in the database."""

    def __init__(self, scheme_name: str):
        detail = f"Weighting scheme ID not found for the provided weighting scheme name: {scheme_name}."
        super().__init__(status_code=404, detail=detail)


class MissingWeightingSchemeError(HTTPException):
    """Raised when neither weighting scheme name nor weighting scheme ID is provided."""

    def __init__(self):
        detail = "Either weighting scheme name or weighting scheme ID must be provided."
        super().__init__(status_code=400, detail=detail)


class UnknownError(HTTPException):
    """
    Raised when an unexpected internal error occurs.

    Returns the error message and stack trace as a list of lines for better readability.
    """

    def __init__(self, error_message: str):
        # Capture the stack trace and split it into a list of lines
        stack_trace = traceback.format_exc().splitlines()

        # Structured error message with separate fields for the error message and stack trace
        detail = {
            "error": f"Internal Server Error: {error_message}",
            "stack_trace": stack_trace  # List of lines, not a single string
        }
        super().__init__(status_code=500, detail=detail)


class ItemNotFoundError(Exception):
    """Custom exception raised when an item_id is not found in the database."""

    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"Item ID {item_id} is not found in the database")


class MissingLCIAValueError(Exception):
    def __init__(
            self,
            item_id: str,
            geo_id: int,
            stage_id: int = None,
            ic_id: int = None,
            table_name: str = "",
            message: str = "Missing LCIA value"
    ):
        self.item_id = item_id
        self.stage_id = stage_id
        self.impact_category_id = ic_id
        self.geo_id = geo_id
        self.table_name = table_name
        self.message = (
            f"{message} in table '{self.table_name}' for item {item_id}, geo {geo_id}, "
            f"stage {stage_id if stage_id else 'N/A'},impact category {ic_id if ic_id else 'N/A'}."
        )
        super().__init__(self.message)


class MultipleMissingLCIAValueErrors(Exception):
    def __init__(self, missing_errors):
        self.missing_errors = missing_errors
        super().__init__(self._generate_message())

    def _generate_message(self):
        messages = [str(error) for error in self.missing_errors]
        return "\n".join(messages)


class NameNotFoundError(Exception):
    def __init__(
            self, name_type: str, identifier_type: str, identifier_value: Union[int, str]
    ):
        message = f"{name_type} not found for {identifier_type} = {identifier_value}"
        super().__init__(message)


class MinMaxValidationError(Exception):
    def __init__(self, scheme_id, field_name, min_value=None, max_value=None, ic_id=None, lc_id=None):
        self.scheme_id = scheme_id
        self.field_name = field_name
        self.min_value = min_value
        self.max_value = max_value
        self.ic_id = ic_id
        self.lc_id = lc_id
        super().__init__(self._generate_message())

    def _generate_message(self):
        if self.ic_id:
            return (f"Validation error for scheme ID {self.scheme_id}: "
                    f"Impact category {self.ic_id} min value {self.min_value} is not less than max value {self.max_value}.")
        if self.lc_id:
            return (f"Validation error for scheme ID {self.scheme_id}: "
                    f"Lifecycle stage {self.lc_id} min value {self.min_value} is not less than max value {self.max_value}.")
        return (f"Validation error for scheme ID {self.scheme_id}: {self.field_name} "
                f"min value {self.min_value} is not less than max value {self.max_value}.")


class GeoNotFoundError(Exception):
    """Custom exception for cases when a geography or country acronym is not found."""

    def __init__(self, message: str):
        super().__init__(message)


if __name__ == "__main__":
    print("This is only a library. Nothing will happen when you execute it")
