import re
from typing import (
    List,
    Dict,
    Union,
    ClassVar,
    Optional,
    Literal,
)

from pydantic import (
    BaseModel,
    field_validator,
    Field,
    model_validator, ConfigDict, model_serializer,
)
from pydantic_core.core_schema import ValidationInfo

from API import exceptions


# Basic configuration models
class BaseConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid', )

    def __init__(self, value):
        # Dynamically determine the field name
        field_name = next(iter(self.model_fields))
        super().__init__(**{field_name: value})

    def get_value(self):
        """
        Dynamically determine the field name and return the instance's field value.
        """
        field_name = next(iter(self.model_fields))
        return getattr(self, field_name)


class ExcludingBaseConfigModel(BaseConfigModel):
    """
    A base class that inherits from BaseConfigModel and is excluded from OpenAPI by default.
    """

    model_config = ConfigDict(json_schema_extra={'include_in_docs': False})


class ExcludingBaseModel(BaseModel):
    """
    A base class that inherits from BaseConfigModel and is excluded from OpenAPI by default.
    """

    model_config = ConfigDict(json_schema_extra={'include_in_docs': False}, extra='forbid', )


class _Weight(BaseModel):
    """
    Base class representing a weight.

    Attributes:

        weight (float):
            The weight ic_weight, must be between 0 and 1 with up to two decimal places.

    Example Usage:

        >>> weight = _Weight(weight=0.75)

    Validators:

        check_value:
            Ensures that the weight ic_weight is between 0 and 1 with up to two decimal places.
    """

    weight: float = Field(
        ...,
        description=(
            "The weight ic_weight, must be between 0 and 1 with up to two decimal"
            " places."
        ),
    )

    validation_context: ClassVar[str] = "Weight"

    @field_validator("weight")
    def check_value(cls, value, info: ValidationInfo):
        context = cls.validation_context
        #TODO add rounding again ?
        if not (0 <= value <= 1):  # and round(value, 2) == value):
            raise ValueError(
                f"{context} must be between 0 and 1 with up to two decimal places."
            )
        return value


class ICWeight(_Weight):
    """
    Class representing the weight of an impact category.

    Inherits from the _Weight base class and represents a specific weight ic_weight
    associated with an impact category in a life cycle inventory (LCI) calculation.

    Attributes:

        weight (float):
            The weight ic_weight, inherited from the _Weight base class, must be between 0 and 1 with up to two decimal places.

    Example Usage:

        >>> ic_weight = ICWeight(weight=0.75)

    Validators:

        check_value:
            Ensures that the weight ic_weight is between 0 and 1 with up to two decimal places.
    """

    validation_context: ClassVar[str] = "IC weights"


class _Weights(BaseModel):
    """
    Class representing a list of weights.

    Attributes:

        weights (List[Union[_Weight, ICWeight, ]]):
            The list of weights. Each weight must be an instance of _Weight, or ICWeight


    Validators:

        validate_weights:
            Ensures that the weights list is not empty and that the sum of all weights is approximately 1.
    """

    weights: List[Union[_Weight, ICWeight]] = Field(
        ...,
        description=(
            "The list of weights. Each weight must be an instance of _Weight, ICWeight"
        ),
    )

    @field_validator("weights")
    def validate_weights(cls, values):
        if not values:
            raise ValueError("Weights list cannot be empty")
        context = values[0].validation_context
        total_weight = sum(weight.weight for weight in values)
        # TODO: change the validation
        if not (0.9999 <= total_weight <= 1.0001):
            raise ValueError(f"{context} must sum to one")
        return values


# IDs
class GeoID(ExcludingBaseConfigModel):
    """
    Class representing a geographical ID.

    Attributes:
        geo_id (int):
            The geographical ID, must be between 1 and 249.

    Example Usage:
         geo = GeoID(geo_id=100)

    Validators:
        check_range:
            Ensures that the geo_id is within the valid range (1 to 249).
    """

    geo_id: int = Field(
        ..., description="The geographical ID, must be between 1 and 249."
    )

    @field_validator("geo_id")
    def check_range(cls, value):
        if not (1 <= value <= 249):
            raise ValueError("GeoID must be between 1 and 249")
        return value


class GroupID(BaseConfigModel):
    group_id: int

    model_config = {
        "title": "GroupID",
        "description": "A schema representing an grouping of different items.",
    }


class ImpactCategoryID(ExcludingBaseConfigModel):
    """
    Class representing an impact category ID.

    Attributes:

        ic_id (int):
            The ID of the impact category, must be between 1 and 17.

    Example Usage:

         impact_category = ImpactCategoryID(ic_id=5)

    Validators:

        check_range:
            Ensures that the impact category ID is within the valid range (1 to 17).
    """

    ic_id: int = Field(
        ..., description="The ID of the impact category, must be between 1 and 17."
    )

    @field_validator("ic_id")
    def check_range(cls, value):
        if not (1 <= value <= 17):
            raise ValueError("ImpactCategoryID must be between 1 and 17")
        return value

    model_config = {
        "title": "ImpactCategoryID",
        "description": (
            "A model representing an impact category ID which must follow a specific"
            " format."
        ),
    }


class ItemID(BaseConfigModel):
    """
    Represents an item identifier that must follow a specific format.

    Fields:
    - item_id (str): The ID of the item, which must be a 4 or 5 digit integer, optionally followed by an underscore
                     and additional digits. This field is required and is validated to ensure it follows the correct format.
    """

    item_id: str = Field(
        ...,
        description=(
            "The ID of the item, must be a 4 or 5 digit integer, optionally followed by"
            " an underscore and more digits."
        ),
    )

    @field_validator("item_id")
    def check_format(cls, value: str) -> str:
        """
        Validates that the `item_id` is in the correct format, which must be a 4 or 5 digit integer optionally followed
        by an underscore and more digits.
        """
        regex = r"^\d{4,5}(?:_\d+)?$"
        if not isinstance(value, str) or not re.match(regex, value):
            raise ValueError(
                "ItemID must be a 4 or 5 digit integer, optionally followed by an"
                " underscore and more digits"
            )
        return value

    model_config = {
        "title": "ItemID",
        "description": (
            "A model representing an item ID that must follow a specific format, requiring 4 or 5 digits, optionally"
            " followed by an underscore and additional digits."
        ),
    }


class LCStageID(ExcludingBaseConfigModel):
    """
    Class representing a stage ID.

    Attributes:

        lc_stage_id (int):
            The ID of the stage, must be between 1 and 6.

    Example Usage:

        >>> stage = LCStageID(stage_id=3)

    Validators:

        check_range:
            Ensures that the stage ID is within the valid range (1 to 6).
    """

    lc_stage_id: int = Field(
        ..., description="The ID of the stage, must be between 1 and 6."
    )

    @field_validator("lc_stage_id")
    def check_range(cls, value):
        if not (1 <= value <= 6):
            raise ValueError("LCStageID must be between 1 and 6")
        return value


class SubgroupID(BaseConfigModel):
    subgroup_id: int

    model_config = {
        "title": "SubgroupID",
        "description": "A schema representing an sub-grouping of different items.",
    }


class WeightingSchemeID(BaseConfigModel):
    scheme_id: int

    model_config = {
        "title": "Weighting Scheme ID",
        "description": "A model representing the ID for a weighting scheme.",
    }


class WeightingSchemeName(BaseConfigModel):
    """
    Class representing a string for impact category weights.

    Attributes:
        weighting_scheme_name (str):
            The string representing the impact category weights.

    Example Usage:
        >>> weighting_scheme_name = WeightingSchemeName(weighting_scheme_name="ef31_r0510")

    """

    weighting_scheme_name: Literal[
        "ef31_r0510",
        "ef31_r0110",
        "ef31_nr",
        "delphi_r0510",
        "delphi_r0110",
        "delphi_nr"
    ] = Field(..., description="The string representing the impact category weights.")


# Input data

class ItemCountryAcronym(BaseConfigModel):
    """
    A class representing a string in the format 'item_id-country_acronym', which combines
    an item's unique identifier with a country acronym.

    The class provides methods for:
    - Validating that the `country_acronym` follows the ISO 3166-1 alpha-3 format (three uppercase letters).

    Attributes:
        item_id_country_acronym (str): A string in the format 'item_id-country_acronym'.

    Example:
        '12345-FRA'
        '67890-USA'
    """

    item_id_country_acronym: str = Field(
        ...,
        description="A string in the format 'item_id-country_acronym', where the country_acronym is an ISO 3166-1 "
                    "alpha-3 code.",
        example="12345-FRA"
    )

    def get_tuple(self) -> tuple:
        """
        Split the raw_string into item_id and country_acronym and return them as a tuple.

        Returns:
            Tuple[str, str]: A tuple containing (item_id, country_acronym).
        """
        return tuple(self.item_id_country_acronym.split("-"))

    @field_validator("item_id_country_acronym")
    def validate_country_acronym(cls, value):
        """
        Validate that the raw_string is in the format 'item_id-country_acronym' and that
        the country_acronym follows the ISO 3166-1 alpha-3 format (three uppercase letters).

        Args:
            value (str): The input raw string to be validated.

        Raises:
            ValueError: If the string is not in the expected format or if the country_acronym is invalid.

        Returns:
            str: The validated raw string.
        """
        try:
            # Split the string into item_id and country_acronym
            item_id, country_acronym = value.split("-")
        except ValueError:
            raise ValueError("Invalid format for 'item_id-country_acronym', expected format 'item_id-alpha3_country'")

        # Validate that country_acronym is in ISO 3166-1 alpha-3 format (three uppercase letters)
        if not re.match(r"^[A-Z]{3}$", country_acronym):
            raise ValueError(f"Invalid country acronym: {country_acronym}. Must be a valid ISO 3166-1 alpha-3 code.")

        return value


class UniqueID(ExcludingBaseModel):
    item_id: Optional[ItemID] = Field(..., description="The ID of the item (string).")
    geo_id: Optional[GeoID] = Field(..., description="The geographic ID (int).")
    item_id_country_acronym: ItemCountryAcronym = Field(...,
                                                        description="The combination of item_id and country_acronym.")

    model_config = {
        "frozen": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ItemID: lambda v: v.item_id,
            GeoID: lambda v: v.geo_id,
            ItemCountryAcronym: lambda v: v.item_id_country_acronym,
        }
    }


class ItemAmount(BaseConfigModel):
    """
    A class to handle item amounts, initialized with a weight.
    """

    amount: float

    @field_validator("amount")
    def check_positive(cls, value):
        if value <= 0:
            raise ValueError("Item amounts must be greater than 0")
        return value


class InputData(BaseModel):
    """
    Represents the input data schema for calculating environmental impact, containing items and a required weighting
    scheme.

    Attributes:
    - items (Dict[str, float]): A dictionary where the keys are strings in the format 'ItemID-CountryAcronym'
      (e.g., '20134-FRA') and the values are the item amounts in kilograms (as floats). This field is required.
    - weighting_scheme (OneOf, optional): One of the following must be provided:
        - weighting_scheme_name (str): A string representing the name of the weighting scheme to use for
          calculating environmental impacts.
        - weighting_scheme_id (int): An integer representing the ID of the weighting scheme to use.
      Exactly one of these fields is required, but not both.

    """

    items: Dict[Union[ItemCountryAcronym, UniqueID], ItemAmount] = Field(
        ...,
        description="A dictionary with either ItemCountryAcronym or UniqueID objects as keys and item amounts as "
                    "values.",
        example={
            "20134-FRA": 1.2,
            "24070-FRA": 0.5
        }
    )
    weighting_scheme_name: Optional[WeightingSchemeName] = Field(
        default=None,
        description="A string representing the weighting scheme name.",
        example="ef31_r0510"
    )
    weighting_scheme_id: Optional[WeightingSchemeID] = Field(
        None,
        description="An integer representing the scheme ID.",
        example="1"
    )

    model_config = ConfigDict(json_schema_extra={
                                  "properties": {
                                      "items": {
                                          "type": "object",
                                          "description": "A dictionary where the keys are strings in the format 'ItemID-CountryAcronym' ("
                                                         "e.g., '20134-FRA'),"
                                                         "and the values are the item amounts as floats (in kilograms).",
                                          "additionalProperties": {
                                              "type": "number",
                                              "description": "The item amount in kilograms."
                                          }
                                      },
                                      "weighting_scheme": {
                                          "oneOf": [
                                              {
                                                  "type": "object",
                                                  "properties": {
                                                      "weighting_scheme_name": {
                                                          "type": "string",
                                                          "description": "A string representing the weighting scheme name."
                                                      }
                                                  },
                                              },
                                              {
                                                  "type": "object",
                                                  "properties": {
                                                      "weighting_scheme_id": {
                                                          "type": "integer",
                                                          "description": "An integer representing the weighting scheme ID."
                                                      }
                                                  },
                                              }
                                          ],
                                          "description": "One of `weighting_scheme_name` or `weighting_scheme_id` must be provided."
                                      }
                                  },
                                  "required": ["items"],
                                  "example": {
                                      "items": {
                                          "20134-FRA": 1.2,
                                          "24070-FRA": 0.5
                                      },
                                      "weighting_scheme_name": "ef31_r0510"
                                  }
                              }
                              )

    @model_validator(mode='before')
    def validate_weighting_scheme(cls, values):
        """
        Validate that only one of `weighting_scheme_name` or `weighting_scheme_id` is provided.
        Raises a ValidationError if both or neither are provided, and applies a default if none is provided.
        """
        weighting_scheme_name = values.get('weighting_scheme_name')
        weighting_scheme_id = values.get('weighting_scheme_id')

        # Apply the default only if both are missing
        if not weighting_scheme_name and not weighting_scheme_id:
            values['weighting_scheme_name'] = WeightingSchemeName("delphi_r0110")
        elif weighting_scheme_name and weighting_scheme_id:
            raise ValueError("Only one of weighting_scheme_name or weighting_scheme_id should be provided, not both.")

        return values

    def __init__(self, **data):
        """
        Handles the transformation of input types during initialization.
        Accepts ItemCountryAcronym or UniqueID as keys and converts them appropriately.
        Also converts float values to ItemAmount and ensures correct initialization of
        weighting_scheme_name and weighting_scheme_id.
        """
        if 'items' in data:
            raw_items = data['items']
            transformed_items = {}
            for key, value in raw_items.items():
                # If the key is a string, assume it's an item-country_acronym and convert it to ItemCountryAcronym
                if isinstance(key, str):
                    item_country_acronym = ItemCountryAcronym(key)
                    transformed_items[item_country_acronym] = ItemAmount(value) if isinstance(value, float) else value
                # If the key is a UniqueID, no transformation is needed
                elif isinstance(key, UniqueID):
                    transformed_items[key] = ItemAmount(value) if isinstance(value, float) else value
                else:
                    raise ValueError(f"Invalid key type: {type(key)}")

            # Replace raw items with transformed items in the data
            data['items'] = transformed_items

        # Convert weighting_scheme_name if provided as a string
        if 'weighting_scheme_name' in data and isinstance(data['weighting_scheme_name'], str):
            data['weighting_scheme_name'] = WeightingSchemeName(data['weighting_scheme_name'])

        # Convert weighting_scheme_id if provided as an int
        if 'weighting_scheme_id' in data and isinstance(data['weighting_scheme_id'], int):
            data['weighting_scheme_id'] = WeightingSchemeID(data['weighting_scheme_id'])

        # Call the BaseModel's init method to process everything else
        super().__init__(**data)


# Processing
class LCIAValue(BaseModel):
    """
    Class representing an LCI ic_weight.

    :param lcia_value: The LCI ic_weight.
    :type lcia_value: float
    """

    lcia_value: float

    def __init__(self, value):
        # Dynamically determine the field name
        field_name = next(iter(self.model_fields))
        super().__init__(**{field_name: value})

    @field_validator("lcia_value")
    def check_non_negative(cls, v):
        if v < 0:
            raise ValueError("LCI ic_weight must be non-negative")
        return v


class LCIAResult(BaseModel):
    """
    A model representing the Life Cycle Impact Assessment (LCIA) result for a specific item, geographical location,
    and scheme. This result includes aggregated values across life cycle stages and impact categories, along with
    normalization counts for impact categories and stages.

    Attributes:
        item_id (ItemID): The ID of the item for which the LCIA result is generated.
        geo_id (GeoID): The geographical ID associated with the LCIA result.
        single_score (LCIAValue): The overall single score of the LCIA result, representing an aggregated impact.
        stage_values (Dict[LCStageID, LCIAValue]): A dictionary where each key is a life cycle stage (LCStageID) and
            the corresponding value is the LCIA value for that stage.
        impact_category_values (Dict[ImpactCategoryID, LCIAValue]): A dictionary where each key is an impact category
            (ImpactCategoryID) and the corresponding value is the LCIA value for that category.
        ic_normalization (Dict[LCStageID, int]): A dictionary where each key is a life cycle stage (LCStageID) and
            the corresponding value is the number of impact categories summed for that stage.
        lc_normalization (Dict[ImpactCategoryID, int]): A dictionary where each key is an impact category
            (ImpactCategoryID) and the corresponding value is the number of life cycle stages summed for that category.
    """

    item_id: ItemID
    geo_id: GeoID
    proxy_flag: bool
    single_score: LCIAValue
    stage_values: Dict[LCStageID, LCIAValue]
    impact_category_values: Dict[ImpactCategoryID, LCIAValue]
    ic_normalization: Dict[LCStageID, int]
    lc_normalization: Dict[ImpactCategoryID, int]


class WeightsDict(BaseModel):
    weights: Dict[ImpactCategoryID, ICWeight]


# Grading

class MinMaxValues(BaseModel):
    scheme_id: WeightingSchemeID
    single_score_max: LCIAValue
    single_score_min: LCIAValue
    ic_mins: Dict[ImpactCategoryID, LCIAValue]
    ic_maxs: Dict[ImpactCategoryID, LCIAValue]
    lc_mins: Dict[LCStageID, LCIAValue]
    lc_maxs: Dict[LCStageID, LCIAValue]

    # Validator for single scores to ensure min < max
    @model_validator(mode='before')
    def check_single_scores(cls, values):
        single_score_min = values.get('single_score_min')
        single_score_max = values.get('single_score_max')
        scheme_id = values.get('scheme_id')
        if single_score_min and single_score_max and single_score_min.lcia_value >= single_score_max.lcia_value:
            raise exceptions.MinMaxValidationError(
                scheme_id=scheme_id.scheme_id,
                field_name='single_score',
                min_value=single_score_min.lcia_value,
                max_value=single_score_max.lcia_value
            )
        return values

    # Validator for impact category min/max values
    @model_validator(mode='before')
    def check_impact_category_min_max(cls, values):
        ic_mins = values.get('ic_mins')
        ic_maxs = values.get('ic_maxs')
        scheme_id = values.get('scheme_id')
        if ic_mins and ic_maxs:
            for ic_id, min_val in ic_mins.items():
                max_val = ic_maxs.get(ic_id)
                if max_val and min_val.lcia_value >= max_val.lcia_value:
                    raise exceptions.MinMaxValidationError(
                        scheme_id=scheme_id.scheme_id,
                        field_name='impact_category',
                        min_value=min_val.lcia_value,
                        max_value=max_val.lcia_value,
                        ic_id=ic_id.ic_id
                    )
        return values

    # Validator for lifecycle stage min/max values
    @model_validator(mode='before')
    def check_lifecycle_stage_min_max(cls, values):
        lc_mins = values.get('lc_mins')
        lc_maxs = values.get('lc_maxs')
        scheme_id = values.get('scheme_id')
        if lc_mins and lc_maxs:
            for lc_id, min_val in lc_mins.items():
                max_val = lc_maxs.get(lc_id)
                if max_val and min_val.lcia_value >= max_val.lcia_value:
                    raise exceptions.MinMaxValidationError(
                        scheme_id=scheme_id.scheme_id,
                        field_name='lifecycle_stage',
                        min_value=min_val.lcia_value,
                        max_value=max_val.lcia_value,
                        lc_id=lc_id.lc_stage_id
                    )
        return values


class GradedLCIAValue(ExcludingBaseModel):
    """
    Class representing an LCI value with an associated grade and scaled value.

    Attributes:
        lcia_value: The raw life cycle inventory value.
        scaled_value: The value adjusted for grading, should be within 0 to 1.
        grade: The grade assigned based on the scaled value, can be None if not graded.
    """
    lcia_value: float = Field(..., description="The raw life cycle inventory value.")
    scaled_value: float = Field(..., description="The scaled life cycle inventory value, adjusted for grading.")
    grade: Union[str, None] = Field(None, description="The grade assigned to the LCI value, can be None if not graded.")

    @field_validator('scaled_value')
    def check_scaled_range(cls, v):
        """
        Ensure the scaled value is between 0 and 1.
        """
        if not (0 <= v <= 1):
            raise ValueError(f"Scaled value of must be between 0 and 1")
        return v

    @classmethod
    def assign_grade(cls, scaled_value: float) -> str:
        """
        Assign a grade based on the scaled value.

        Grades are determined by the following scale:
        - 'A' for scaled_value < 0.1
        - 'B' for 0.1 <= scaled_value < 0.3
        - 'C' for 0.3 <= scaled_value < 0.5
        - 'D' for 0.5 <= scaled_value < 0.7
        - 'E' for scaled_value >= 0.7
        """
        if scaled_value >= 0.7:
            return "E"
        elif scaled_value >= 0.5:
            return "D"
        elif scaled_value >= 0.3:
            return "C"
        elif scaled_value >= 0.1:
            return "B"
        else:
            return "A"


class GradedLCIAResult(ExcludingBaseModel):
    """
    Class representing the result of an LCI calculation with graded values, optionally including an item ID.
    """
    item_id: Optional[ItemID] = Field(default=None, description="The ID of the item this result pertains to, optional.")
    geo_id: Optional[GeoID] = Field(default=None)
    proxy_flag: bool
    single_score: GradedLCIAValue
    stage_values: Dict[LCStageID, GradedLCIAValue]
    impact_category_values: Dict[ImpactCategoryID, GradedLCIAValue]


# Output

class ItemInfo(BaseModel):
    """
    Represents detailed information about a product item, including its product name, country, and classification.

    Fields:
    - product_name (str): The name of the product (e.g., 'Lamb, neck, braised or boiled').
    - country (str): The name of the country where the product originates (e.g., 'France').
    - international_code (int): The numeric international code for the country (e.g., 250 for France, based on ISO 3166).
    - group (Optional[str]): The main category or group to which the product belongs (e.g., 'viandes, œufs, poissons').
    - subgroup (Optional[str]): The subcategory of the product within its group (e.g., 'viandes cuites').
    - proxy (bool): Indicates whether the data for this item is a proxy (i.e., estimated or inferred data).
                  `True` means it is a proxy, `False` means it is not.

    """
    composite_key: str

    product_name: str = Field(
        ...,
        description="The name of the product (e.g., 'Lamb, neck, braised or boiled')."
    )
    country: str = Field(
        ...,
        description="The name of the country where the product originates (e.g., 'France')."
    )
    international_code: int = Field(
        ...,
        description="The numeric international code for the country (e.g., 250 for France, based on ISO 3166)."
    )
    group: Optional[str] = Field(
        None,
        description="The main category or group to which the product belongs (e.g., 'viandes, œufs, poissons')."
    )
    subgroup: Optional[str] = Field(
        None,
        description="The subcategory of the product within its group (e.g., 'viandes cuites')."
    )
    proxy: bool = Field(
        ...,
        description="Indicates whether the data for this item is a proxy (i.e., estimated or inferred data). "
                    "`True` means it is a proxy, `False` means it is not."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_name": "Lamb, neck, braised or boiled",
                "country": "France",
                "international_code": 250,
                "group": "viandes, œufs, poissons",
                "subgroup": "viandes cuites",
                "proxy": False
            }
        }
    }


class AllItems(BaseModel):
    """
    Represents a collection of items, where each item is serialized into a dictionary format with composite keys.

    Fields:
    - items (List[ItemInfo]): A list of `ItemInfo` objects representing individual items, where each item contains
          detailed product information such as `product_name`, `country`, `group`, and whether it is a proxy.

    Returns:
        A dictionary where each key is a composite string (e.g., 'itemid-country_acronym'), and each value is the
        corresponding product information.
    """

    items: List[ItemInfo] = Field(
        ...,
        description="A list of `ItemInfo` objects, where each item contains detailed information such as product name, "
                    "country, and proxy status."
    )

    @model_serializer
    def model_dump(self, **kwargs):
        """
        Custom serialization method to return the desired dictionary format
        where keys are composite keys ('itemid-geoid') and values are the item info.
        """
        result = {}
        for item in self.items:
            # Use the composite_key as the key for the serialized output
            result[item.composite_key] = item.dict(exclude={"composite_key"})
        return result

    model_config = {
        "json_schema_extra": {
            "example": {
                "21508-FRA": {
                    "product_name": "Lamb, neck, braised or boiled",
                    "country": "France",
                    "country_code": 250,
                    "group": "viandes, œufs, poissons",
                    "subgroup": "viandes cuites",
                    "proxy": False
                },
                "21519-FRA": {
                    "product_name": "Lamb, leg, braised",
                    "country": "France",
                    "country_code": 250,
                    "group": "viandes, œufs, poissons",
                    "subgroup": "viandes cuites",
                    "proxy": False
                }
            }
        }
    }


class OutputData(BaseModel):
    """
    Represents the output data after calculating the environmental impact of a recipe.

    The output contains detailed results, including aggregated scores for life cycle stages and impact categories,
    as well as a single score for both the entire recipe and individual items.

    The output is serialized into a structured format with the following fields:

    Fields:
    - Recipe Info (dict): General information about the recipe, including the weighting scheme, total mass, and single score.
        - General Info (dict): Contains:
            - Weighting Scheme (str): The name of the weighting scheme used for the calculation.
            - contains_proxy (bool): Indicates whether proxy data is present in any item or stage.
            - Overall Mass (str): The total mass of the recipe in kilograms.
        - Single Score (dict): Contains:
            - Single Score (float): The overall environmental impact score for the entire recipe.
            - Grade (str): A letter grade representing the performance (e.g., "A").
            - Scaled Value (float): The normalized and scaled score between 0 and 1.
        - Items (dict): A dictionary where the keys are item identifiers (in the format `itemid-country_acronym`)
                        and the values are the item amounts in kilograms.
        - Stages (dict): A dictionary where the keys are life cycle stage names (e.g., "Agriculture") and the values are:
            - lcia_value (float): The environmental impact value for the stage.
            - Grade (str): The grade for the stage (e.g., "B").
            - Scaled Value (float): The scaled environmental impact value for the stage.
        - Impact Categories (dict): A dictionary where the keys are impact category names (e.g., "Climate Change") and the values are:
            - lcia_value (float): The environmental impact value for the category.
            - Grade (str): The grade for the category (e.g., "A").
            - Scaled Value (float): The scaled environmental impact value for the category.

    - Item Results (dict): Contains detailed environmental impact results for each item in the recipe.
        Each key is an item identifier (in the format `itemid-country_acronym`) and the values contain:
        - Single Score (dict): The environmental impact score for the individual item.
        - Stages (dict): The environmental impact score for each life cycle stage, structured similarly to the `Stages` field.
        - Impact Categories (dict): The environmental impact score for each impact category, structured similarly to the `Impact Categories` field.
        - contains_proxy (bool): Indicates whether proxy data is used for the item.
    """
    input_data: InputData = Field(..., exclude=True)
    graded_lcia_results: List[GradedLCIAResult] = Field(..., exclude=True)
    recipe_scores: GradedLCIAResult = Field(..., exclude=True)
    proxy_flags: Dict[UniqueID, bool] = Field(..., exclude=True)
    stage_names: Dict[LCStageID, str] = Field(..., exclude=True)
    impact_category_names: Dict[ImpactCategoryID, str] = Field(..., exclude=True)

    @model_serializer
    def model_dump(self, **kwargs):
        """
        Custom serialization method to restructure the output without altering the internal fields.
        """
        # Simplify custom serialization to avoid complex logic in this function
        contains_proxy = any(self.proxy_flags.values())
        overall_mass = sum(
            self.input_data.items[item_id].amount for item_id in self.input_data.items
        )

        # Build recipe info
        recipe_info = {
            "General Info": {
                "Weighting Scheme": self.input_data.weighting_scheme_name.get_value(),
                "contains_proxy": contains_proxy,
                "Overall Mass": f"{overall_mass} kg"
            },
            "Single Score": {
                "Single Score": self.recipe_scores.single_score.lcia_value,
                "Grade": self.recipe_scores.single_score.grade,
                "Scaled Value": self.recipe_scores.single_score.scaled_value
            },
            "Items": {
                unique_id.item_id_country_acronym.item_id_country_acronym: f"{amount.amount} kg"
                for unique_id, amount in self.input_data.items.items()
            },
            "Stages": {
                self.stage_names[stage_id]: {
                    "lcia_value": stage_value.lcia_value,
                    "Grade": stage_value.grade,
                    "Scaled Value": stage_value.scaled_value
                } for stage_id, stage_value in self.recipe_scores.stage_values.items()
            },
            "Impact Categories": {
                self.impact_category_names[ic_id]: {
                    "lcia_value": ic_value.lcia_value,
                    "Grade": ic_value.grade,
                    "Scaled Value": ic_value.scaled_value
                } for ic_id, ic_value in self.recipe_scores.impact_category_values.items()
            }
        }

        # Return serialized output
        return {
            "Recipe Info": recipe_info,
            "Item Results": {
                unique_id.item_id_country_acronym.item_id_country_acronym: {
                    "Single Score": {
                        "Single Score": item_result.single_score.lcia_value,
                        "Grade": item_result.single_score.grade,
                        "Scaled Value": item_result.single_score.scaled_value,
                        "contains_proxy": self.proxy_flags[unique_id]
                    },
                    "Stages": {
                        self.stage_names[stage_id]: {
                            "lcia_value": stage_value.lcia_value,
                            "Grade": stage_value.grade,
                            "Scaled Value": stage_value.scaled_value
                        } for stage_id, stage_value in item_result.stage_values.items()
                    },
                    "Impact Categories": {
                        self.impact_category_names[ic_id]: {
                            "lcia_value": ic_value.lcia_value,
                            "Grade": ic_value.grade,
                            "Scaled Value": ic_value.scaled_value
                        } for ic_id, ic_value in item_result.impact_category_values.items()
                    }
                } for unique_id, item_result in zip(self.proxy_flags.keys(), self.graded_lcia_results)
            }
        }

    # Retain the schema definition for OpenAPI docs
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Recipe Info": {
                    "General Info": {
                        "Weighting Scheme": "ef31_r0510",
                        "contains_proxy": False,
                        "Overall Mass": "float_value kg"
                    },
                    "Single Score": {
                        "Single Score": "float_value",
                        "Grade": "A",
                        "Scaled Value": "float_value"
                    },
                    "Items": {
                        "20134-FRA": "float_value kg",
                        "more_items": "..."
                    },
                    "Stages": {
                        "Agriculture": {
                            "lcia_value": "float_value",
                            "Grade": "B",
                            "Scaled Value": "float_value"
                        },
                        "more_stages": "..."
                    },
                    "Impact Categories": {
                        "Climate change": {
                            "lcia_value": "float_value",
                            "Grade": "A",
                            "Scaled Value": "float_value"
                        },
                        "more_impact_categories": "..."
                    }
                },
                "Item Results": {
                    "20134-FRA": {
                        "Single Score": {
                            "Single Score": "float_value",
                            "Grade": "A",
                            "Scaled Value": "float_value",
                            "contains_proxy": False
                        },
                        "Stages": {
                            "Agriculture": {
                                "lcia_value": "float_value",
                                "Grade": "B",
                                "Scaled Value": "float_value"
                            },
                            "more_stages": "..."
                        },
                        "Impact Categories": {
                            "Climate change": {
                                "lcia_value": "float_value",
                                "Grade": "A",
                                "Scaled Value": "float_value"
                            },
                            "more_impact_categories": "..."
                        }
                    },
                    "more_items": "..."
                }
            }
        }
    )


if __name__ == "__main__":
    print("This is only a library. Nothing will happen when you execute it")
