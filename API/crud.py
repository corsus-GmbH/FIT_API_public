"""
This module provides CRUD operations for interacting with the database.
It includes functions to fetch LCI values, stage IDs, and impact category IDs.
"""

from typing import (
    List,
    Union, Dict, Tuple, Set,
)

import pydantic
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import (
    Session,
    select,
    func,

)

from API import (
    schemas,
    models,
    exceptions,
)


def get_min_max_values(
        session: Session,
        scheme_id: schemas.WeightingSchemeID,
        impact_category_ids: List[schemas.ImpactCategoryID],
        lc_stage_ids: List[schemas.LCStageID]
) -> schemas.MinMaxValues:
    """
    Get maximal and minimal values for single scores, specified impact categories,
    and lifecycle stages for a given scheme ID.

    Args:
        session (Session): The database session.
        scheme_id (schemas.WeightingSchemeID): The scheme ID.
        impact_category_ids (List[schemas.ImpactCategoryID]): List of impact category IDs.
        lc_stage_ids (List[schemas.LCStageID]): List of lifecycle stage IDs.

    Returns:
        schemas.MinMaxValues: An object containing maximal and minimal values for single scores,
        impact categories, and lifecycle stages.

    Raises:
        ValueError: If there is a validation error in the Pydantic models.
        SQLAlchemyError: If a database error occurs.
        exceptions.MinMaxValueNotFoundError: If min or max values are not found.
        exceptions.UnknownError: If an unknown error occurs.
    """
    try:
        # Fetch max and min values for single scores
        single_score_query = (
            select(
                func.max(models.SingleScores.single_score),
                func.min(models.SingleScores.single_score)
            )
            .where(
                models.SingleScores.scheme_id == scheme_id.scheme_id
            )
        )
        single_score_result = session.exec(single_score_query).first()
        if not single_score_result or single_score_result[0] is None or single_score_result[1] is None:
            raise exceptions.MinMaxValueNotFoundError("Single Score", "N/A", scheme_id.scheme_id)

        single_score_max = single_score_result[0]
        single_score_min = single_score_result[1]

        # Initialize dictionaries for impact category and lifecycle stage min and max values
        ic_mins = {}
        ic_maxs = {}
        lc_mins = {}
        lc_maxs = {}

        # Fetch max and min values for each impact category
        for impact_category_id in impact_category_ids:
            impact_category_query = (
                select(
                    func.max(models.WeightedResults.weighted_value),
                    func.min(models.WeightedResults.weighted_value)
                )
                .where(
                    (models.WeightedResults.ic_id == impact_category_id.ic_id) &
                    (models.WeightedResults.scheme_id == scheme_id.scheme_id)
                )
            )
            impact_category_result = session.exec(impact_category_query).first()
            if not impact_category_result or impact_category_result[0] is None or impact_category_result[1] is None:
                raise exceptions.MinMaxValueNotFoundError(
                    "Impact Category", impact_category_id.ic_id, scheme_id.scheme_id
                )

            ic_maxs[impact_category_id] = schemas.LCIAValue(impact_category_result[0])
            ic_mins[impact_category_id] = schemas.LCIAValue(impact_category_result[1])

        # Fetch max and min values for each lifecycle stage
        for lifecycle_stage_id in lc_stage_ids:
            lifecycle_stage_query = (
                select(
                    func.max(models.WeightedResults.weighted_value),
                    func.min(models.WeightedResults.weighted_value)
                )
                .where(
                    (models.WeightedResults.lc_stage_id == lifecycle_stage_id.lc_stage_id) &
                    (models.WeightedResults.scheme_id == scheme_id.scheme_id)
                )
            )
            lifecycle_stage_result = session.exec(lifecycle_stage_query).first()
            if not lifecycle_stage_result or lifecycle_stage_result[0] is None or lifecycle_stage_result[1] is None:
                raise exceptions.MinMaxValueNotFoundError(
                    "Lifecycle Stage", lifecycle_stage_id.lc_stage_id, scheme_id.scheme_id
                )

            lc_maxs[lifecycle_stage_id] = schemas.LCIAValue(lifecycle_stage_result[0])
            lc_mins[lifecycle_stage_id] = schemas.LCIAValue(lifecycle_stage_result[1])

        # Return the MinMaxValues schema with the computed values
        return schemas.MinMaxValues(
            scheme_id=scheme_id,
            single_score_max=schemas.LCIAValue(single_score_max),
            single_score_min=schemas.LCIAValue(single_score_min),
            ic_mins=ic_mins,
            ic_maxs=ic_maxs,
            lc_mins=lc_mins,
            lc_maxs=lc_maxs
        )

    except pydantic.ValidationError as validation_error:
        raise ValueError(f"Validation error occurred while processing min and max values: {str(validation_error)}")
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error occurred: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_ic_weights_by_scheme_id(
        session: Session,
        scheme: schemas.WeightingSchemeID
) -> schemas.WeightsDict:
    """
    Fetches and validates the impact category weights for a given scheme ID.

    Args:
        session (Session): The database session.
        scheme (schemas.WeightingSchemeID): The scheme ID for which to fetch weights.

    Returns:
        schemas.WeightsDict: A dictionary with ImpactCategoryID as keys and ICWeight as values.

    Raises:
        exceptions.NameNotFoundError: If no weights are found for the given scheme ID.
        ValueError: If weights do not sum to approximately 1.0 or if validation fails.
        SQLAlchemyError: If there is a database error during query execution.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Query to retrieve impact category weights for the given scheme ID
        query = select(
            models.ImpactCategoryWeights
        ).where(
            (models.ImpactCategoryWeights.scheme_id == scheme.scheme_id) &
            (models.ImpactCategoryWeights.ic_weight > 0)
        )
        results = session.exec(query).all()

        # Raise error if no weights are found for the scheme
        if not results:
            raise exceptions.NameNotFoundError(
                name_type="Weights",
                identifier_type="scheme ID",
                identifier_value=str(scheme.scheme_id)
            )

        # Construct weights dictionary and validate ImpactCategoryID and ICWeight schema
        try:
            weights_dict = {
                schemas.ImpactCategoryID(result.ic_id): schemas.ICWeight(weight=result.ic_weight)
                for result in results
            }
        except pydantic.ValidationError as validation_error:
            raise ValueError(f"Invalid data for impact category weights: {str(validation_error)}")

        # Validate that weights sum approximately to 1
        try:
            schemas._Weights(weights=list(weights_dict.values()))
        except pydantic.ValidationError as validation_error:
            raise ValueError(
                f"Weights do not sum to one: {str(validation_error)}"
            )
        return schemas.WeightsDict(weights=weights_dict)

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error occurred while fetching weights: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_name_by_id(
        session: Session,
        id_schema: Union[
            schemas.LCStageID,
            schemas.ImpactCategoryID,
            schemas.GeoID,
            schemas.ItemID,
            schemas.GroupID,
            schemas.SubgroupID,
            schemas.WeightingSchemeID,
        ],
) -> str:
    """
    Retrieve a name associated with a specific ID schema from the appropriate table.

    Args:
        session (Session): The database session.
        id_schema (Union[schemas.LCStageID, schemas.ImpactCategoryID, schemas.GeoID,
                         schemas.ItemID, schemas.GroupID, schemas.SubgroupID, schemas.WeightingSchemeID]):
            An instance of a Pydantic schema representing the ID to fetch.

    Returns:
        str: The name associated with the provided ID.

    Raises:
        exceptions.NameNotFoundError: If no entry is found for the given ID schema.
        ValueError: If an invalid ID schema is provided.
        SQLAlchemyError: If there is a database error during the query execution.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        if isinstance(id_schema, schemas.LCStageID):
            return fetch_from_life_cycle_stages(session, id_schema)
        elif isinstance(id_schema, schemas.ImpactCategoryID):
            return fetch_from_impact_categories(session, id_schema)
        elif isinstance(id_schema, schemas.GeoID):
            return fetch_from_geographies(session, id_schema)
        elif isinstance(id_schema, schemas.ItemID):
            return fetch_from_metadata(session, id_schema)
        elif isinstance(id_schema, schemas.GroupID):
            return fetch_from_groups(session, id_schema)
        elif isinstance(id_schema, schemas.SubgroupID):
            return fetch_from_subgroups(session, id_schema)
        elif isinstance(id_schema, schemas.WeightingSchemeID):
            return fetch_from_weighting_schemes(session, id_schema)
        else:
            raise ValueError("Invalid ID schema provided")
    except exceptions.NameNotFoundError as e:
        raise e
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error occurred: {str(db_error)}")
    except pydantic.ValidationError as validation_error:
        raise ValueError(f"Validation error in provided ID schema: {str(validation_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def fetch_from_weighting_schemes(session: Session, scheme_id: schemas.WeightingSchemeID) -> str:
    """Fetch the name of a weighting scheme based on the provided scheme ID."""
    try:
        result = session.exec(
            select(models.WeightingSchemes).where(models.WeightingSchemes.scheme_id == scheme_id.scheme_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("Weighting scheme name", "scheme_id", scheme_id.scheme_id)
        return result.name
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching weighting scheme: {str(db_error)}")


def fetch_from_groups(session: Session, group_id: schemas.GroupID) -> str:
    """Fetch the name of a group based on the provided group ID."""
    try:
        result = session.exec(
            select(models.Groups).where(models.Groups.group_id == group_id.group_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("Group name", "group_id", group_id.group_id)
        return result.group_name
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching group: {str(db_error)}")


def fetch_from_subgroups(session: Session, subgroup_id: schemas.SubgroupID) -> str:
    """Fetch the name of a subgroup based on the provided subgroup ID."""
    try:
        result = session.exec(
            select(models.Subgroups).where(models.Subgroups.subgroup_id == subgroup_id.subgroup_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("Subgroup name", "subgroup_id", subgroup_id.subgroup_id)
        return result.subgroup_name
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching subgroup: {str(db_error)}")


def fetch_from_life_cycle_stages(session: Session, stage_id: schemas.LCStageID) -> str:
    """Fetch the name of a lifecycle stage based on the provided stage ID."""
    try:
        result = session.exec(
            select(models.LifeCycleStages).where(models.LifeCycleStages.lc_stage_id == stage_id.lc_stage_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("Stage name", "lc_stage_id", stage_id.lc_stage_id)
        return result.lc_name
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching lifecycle stage: {str(db_error)}")


def fetch_from_impact_categories(session: Session, impact_category_id: schemas.ImpactCategoryID) -> str:
    """Fetch the name of an impact category based on the provided impact category ID."""
    try:
        result = session.exec(
            select(models.ImpactCategories).where(models.ImpactCategories.ic_id == impact_category_id.ic_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("Impact category name", "ic_id", impact_category_id.ic_id)
        return result.ic_name
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching impact category: {str(db_error)}")


def fetch_from_geographies(session: Session, geo_id: schemas.GeoID) -> str:
    """Fetch the name of a country or geographic region based on the provided geo ID."""
    try:
        result = session.exec(
            select(models.Geographies).where(models.Geographies.geo_id == geo_id.geo_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("Country name", "geo_id", geo_id.geo_id)
        return result.country_name
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching geography: {str(db_error)}")


def fetch_from_metadata(session: Session, item_id: schemas.ItemID) -> str:
    """Fetch the name of an item based on the provided item ID."""
    try:
        result = session.exec(
            select(models.MetaData).where(models.MetaData.item_id == item_id.item_id)
        ).first()
        if not result:
            raise exceptions.NameNotFoundError("LCI name", "item_id", item_id.item_id)
        return result.name_lci
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in fetching item metadata: {str(db_error)}")


def get_country_acronym_by_geoid(session: Session, geoid: schemas.GeoID) -> str:
    """
    Get the country_acronym (geo_shorthand_3) from a given GeoID instance.
    Raises GeoNotFoundError if the country_acronym is not found.
    """
    geo_id_value = geoid.get_value()
    statement = select(models.Geographies.geo_shorthand_3).where(models.Geographies.geo_id == geo_id_value)
    result = session.exec(statement).first()

    if result is None:
        raise exceptions.GeoNotFoundError(f"Country acronym not found for GeoID: {geo_id_value}.")

    return result


def get_geoid_by_country_acronym(session: Session, country_acronym: str) -> schemas.GeoID:
    """
    Retrieve a GeoID instance from the database using a given country acronym.

    Args:
        session (Session): The database session.
        country_acronym (str): The 3-letter country acronym (geo_shorthand_3).

    Returns:
        schemas.GeoID: A GeoID instance corresponding to the given country acronym.

    Raises:
        exceptions.GeoNotFoundError: If no GeoID is found for the given country acronym.
        SQLAlchemyError: If a database error occurs during query execution.
        ValueError: If the retrieved GeoID data is invalid according to Pydantic validation.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Query the database for the GeoID using the country acronym
        statement = select(models.Geographies.geo_id).where(models.Geographies.geo_shorthand_3 == country_acronym)
        result = session.exec(statement).first()

        # Raise GeoNotFoundError if no result is found
        if result is None:
            raise exceptions.GeoNotFoundError(f"GeoID not found for country acronym: '{country_acronym}'.")

        # Attempt to instantiate GeoID schema with the result to ensure it’s valid
        try:
            return schemas.GeoID(result)
        except pydantic.ValidationError as validation_error:
            raise ValueError(f"Invalid GeoID data retrieved: {str(validation_error)}")

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error occurred while fetching GeoID for acronym '{country_acronym}': {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_scheme_id_by_weight_string(
        session: Session,
        weights_string: schemas.WeightingSchemeName
) -> schemas.WeightingSchemeID:
    """
    Retrieve the scheme ID for a given weighting scheme name from the database.

    Args:
        session (Session): The database session.
        weights_string (schemas.WeightingSchemeName): A Pydantic model containing the weighting scheme name.

    Returns:
        schemas.WeightingSchemeID: A Pydantic model instance containing the scheme ID.

    Raises:
        exceptions.NameNotFoundError: If no weighting scheme is found for the given name.
        SQLAlchemyError: If a database error occurs during query execution.
        ValueError: If the retrieved scheme ID is invalid according to Pydantic validation.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Query to find the scheme ID for the provided weighting scheme name
        query = select(models.WeightingSchemes.scheme_id).where(
            models.WeightingSchemes.name == weights_string.weighting_scheme_name
        )
        result = session.exec(query).one_or_none()

        # Raise error if no result is found
        if result is None:
            raise exceptions.NameNotFoundError(
                name_type="Scheme ID",
                identifier_type="weight string",
                identifier_value=weights_string.weighting_scheme_name
            )

        # Attempt to instantiate WeightingSchemeID with the result for validation
        try:
            return schemas.WeightingSchemeID(result)
        except pydantic.ValidationError as validation_error:
            raise ValueError(f"Invalid Scheme ID data retrieved: {str(validation_error)}")

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error occurred while fetching Scheme ID for weighting scheme name '{weights_string.weighting_scheme_name}': {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_proxy_flag(session: Session, item_id: schemas.ItemID, geo_id: schemas.GeoID) -> bool:
    """
    Retrieve the proxy flag from the MetaData table for a given item ID and geo ID.

    Args:
        session (Session): The database session.
        item_id (schemas.ItemID): The item ID, as a Pydantic schema.
        geo_id (schemas.GeoID): The geographical ID, as a Pydantic schema.

    Returns:
        bool: The proxy flag value (True/False) for the specified item and geo ID.

    Raises:
        exceptions.NameNotFoundError: If no metadata is found for the specified item_id and geo_id.
        SQLAlchemyError: If a database error occurs during query execution.
        ValueError: If the retrieved proxy flag data is invalid according to Pydantic validation.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        query = select(models.MetaData.proxy_flag).where(
            (models.MetaData.item_id == item_id.get_value()) &
            (models.MetaData.geo_id == geo_id.get_value())
        )
        result = session.exec(query).first()

        # Raise NameNotFoundError if no result is found
        if result is None:
            raise exceptions.NameNotFoundError(
                "Proxy flag", "item_id and geo_id", f"{item_id.get_value()} and {geo_id.get_value()}"
            )

        # Ensure the result is valid as a boolean
        if not isinstance(result, bool):
            raise ValueError(
                f"Invalid proxy flag data retrieved for item_id: {item_id.get_value()} and geo_id: {geo_id.get_value()}")

        return result

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error while fetching proxy flag for item_id: {item_id.get_value()} and geo_id: {geo_id.get_value()}: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def fetch_results_from_weighted_results(
        session: Session,
        item_id: schemas.ItemID,
        geo_id: schemas.GeoID,
        scheme_id: schemas.WeightingSchemeID,
        expected_combinations: Set[Tuple[schemas.ImpactCategoryID, schemas.LCStageID]]
) -> Dict[Tuple[schemas.ImpactCategoryID, schemas.LCStageID], schemas.LCIAValue]:
    """
    Fetch LCIA values for the specified impact category and life cycle stage combinations
    from the WeightedResults table.

    Args:
        session (Session): The database session.
        item_id (schemas.ItemID): The item ID, as a Pydantic schema.
        geo_id (schemas.GeoID): The geographical ID, as a Pydantic schema.
        scheme_id (schemas.WeightingSchemeID): The scheme ID, as a Pydantic schema.
        expected_combinations (Set[Tuple[schemas.ImpactCategoryID, schemas.LCStageID]]):
            A set of expected (ImpactCategoryID, LCStageID) tuples.

    Returns:
        Dict[Tuple[schemas.ImpactCategoryID, schemas.LCStageID], schemas.LCIAValue]:
            A dictionary mapping each (ImpactCategoryID, LCStageID) combination to its LCIA value.

    Raises:
        exceptions.MissingLCIAValueError: If no results are found for the specified combinations.
        SQLAlchemyError: If a database error occurs during query execution.
        ValueError: If the retrieved LCIA values are invalid according to Pydantic validation.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Decompose expected combinations into IC and LC stage IDs for filtering
        ic_ids = {ic_id.ic_id for ic_id, _ in expected_combinations}
        lc_stage_ids = {lc_stage.lc_stage_id for _, lc_stage in expected_combinations}

        # Query the database for matching results in WeightedResults
        query = select(
            models.WeightedResults.ic_id,
            models.WeightedResults.lc_stage_id,
            models.WeightedResults.weighted_value
        ).where(
            (models.WeightedResults.item_id == item_id.item_id) &
            (models.WeightedResults.geo_id == geo_id.geo_id) &
            (models.WeightedResults.scheme_id == scheme_id.scheme_id) &
            (models.WeightedResults.ic_id.in_(ic_ids)) &
            (models.WeightedResults.lc_stage_id.in_(lc_stage_ids))
        )

        results = session.exec(query).all()

        # Raise error if no results are found
        if not results:
            raise exceptions.MissingLCIAValueError(
                item_id=item_id.item_id,
                stage_id=None,
                ic_id=None,
                geo_id=geo_id.geo_id,
                table_name="WeightedResults"
            )

        # Construct result dictionary with schema validation
        try:
            result_dict = {
                (schemas.ImpactCategoryID(ic_id), schemas.LCStageID(lc_stage_id)): schemas.LCIAValue(value)
                for ic_id, lc_stage_id, value in results
            }
        except pydantic.ValidationError as validation_error:
            raise ValueError(f"Invalid LCIA value data retrieved: {str(validation_error)}")

        return result_dict

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error while fetching weighted results for item_id: {item_id.item_id}, geo_id: {geo_id.geo_id}, and scheme_id: {scheme_id.scheme_id}: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def fetch_result_from_single_scores(
        session: Session,
        item_id: schemas.ItemID,
        geo_id: schemas.GeoID,
        scheme_id: schemas.WeightingSchemeID
) -> schemas.LCIAValue:
    """
    Fetch the LCIA value from the SingleScores table for a specific item, geo, and scheme combination.

    Args:
        session (Session): The database session.
        item_id (schemas.ItemID): The item ID, as a Pydantic schema.
        geo_id (schemas.GeoID): The geographical ID, as a Pydantic schema.
        scheme_id (schemas.WeightingSchemeID): The scheme ID, as a Pydantic schema.

    Returns:
        schemas.LCIAValue: The fetched LCIA value.

    Raises:
        exceptions.MissingLCIAValueError: If no LCIA value is found for the specified combination.
        SQLAlchemyError: If a database error occurs during query execution.
        ValueError: If the retrieved LCIA value is invalid according to Pydantic validation.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Query to retrieve the single score for the specified combination
        query = select(models.SingleScores.single_score).where(
            (models.SingleScores.item_id == item_id.item_id) &
            (models.SingleScores.geo_id == geo_id.geo_id) &
            (models.SingleScores.scheme_id == scheme_id.scheme_id)
        )

        result = session.exec(query).first()

        # Raise MissingLCIAValueError if no result is found
        if result is None:
            raise exceptions.MissingLCIAValueError(
                item_id=item_id.item_id,
                stage_id=None,
                ic_id=None,
                geo_id=geo_id.geo_id,
                table_name="SingleScores"
            )

        # Validate and return LCIA value using the schema
        try:
            return schemas.LCIAValue(result)
        except pydantic.ValidationError as validation_error:
            raise ValueError(f"Invalid LCIA value retrieved: {str(validation_error)}")

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error occurred while fetching single score for item_id: {item_id.item_id}, "
            f"geo_id: {geo_id.geo_id}, scheme_id: {scheme_id.scheme_id}: {str(db_error)}"
        )
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_item_info(session: Session, item_id: schemas.ItemID, geo_id: schemas.GeoID) -> schemas.ItemInfo:
    """
    Fetch and return item information for a given item and geo_id.

    Args:
        session (Session): The database session.
        item_id (schemas.ItemID): The item ID, following the required format.
        geo_id (schemas.GeoID): The geographic ID.

    Returns:
        schemas.ItemInfo: The item information object.

    Raises:
        ValueError: If the item or supporting information is not found.
        SQLAlchemyError: If a database error occurs during query execution.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Fetch data for the item from the MetaData model
        statement = select(
            models.MetaData.item_id,
            models.MetaData.geo_id,
            models.MetaData.name_lci,
            models.MetaData.group_id,
            models.MetaData.subgroup_id,
            models.MetaData.proxy_flag
        ).where(
            models.MetaData.item_id == item_id.get_value(),
            models.MetaData.geo_id == geo_id.get_value()
        )
        result = session.exec(statement).first()

        if not result:
            raise ValueError(f"Item with ID {item_id.get_value()} and geo ID {geo_id.get_value()} not found.")

        # Fetch supporting information like country name, group name, etc.
        country_acronym = get_country_acronym_by_geoid(session, geo_id)
        country_name = get_name_by_id(session, geo_id)
        group_name = get_name_by_id(session, schemas.GroupID(result.group_id)) if result.group_id else None
        subgroup_name = get_name_by_id(session, schemas.SubgroupID(result.subgroup_id)) if result.subgroup_id else None

        # Create the composite key
        composite_key = f"{result.item_id}-{country_acronym}"

        # Create and return the ItemInfo object
        return schemas.ItemInfo(
            composite_key=composite_key,
            product_name=result.name_lci,
            country=country_name,
            international_code=get_international_code_by_geoid(session, geo_id),
            group=group_name,
            subgroup=subgroup_name,
            proxy=result.proxy_flag
        )

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error while fetching item information for item_id: {item_id.get_value()} and geo_id: {geo_id.get_value()}: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_all_items_info(session: Session) -> schemas.AllItems:
    """
    Return an AllItems object containing a list of ItemInfo objects.

    Args:
        session (Session): The database session.

    Returns:
        schemas.AllItems: An object representing a list of schemas.ItemInfo objects.

    Raises:
        SQLAlchemyError: If a database error occurs during query execution.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        # Fetch all item and geo IDs from the MetaData model
        statement = select(models.MetaData.item_id, models.MetaData.geo_id)
        results = session.exec(statement).all()

        items: List[schemas.ItemInfo] = []

        # Loop through all items and fetch detailed information using the new helper function
        for result in results:
            item_info = get_item_info(session, schemas.ItemID(result.item_id), schemas.GeoID(result.geo_id))
            items.append(item_info)

        # Return an AllItems object with the list of ItemInfo objects
        return schemas.AllItems(items=items)

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error occurred while fetching all item information: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


def get_international_code_by_geoid(session: Session, geo_id: schemas.GeoID) -> int:
    """
    Get the international code for a given geo_id.

    Args:
        session (Session): The database session.
        geo_id (schemas.GeoID): The geo_id to look up the international code.

    Returns:
        int: The international code if found.

    Raises:
        ValueError: If no international code is found for the given geo_id.
        SQLAlchemyError: If a database error occurs during query execution.
        exceptions.UnknownError: If an unexpected error occurs.
    """
    try:
        statement = select(models.Geographies.international_code).where(models.Geographies.geo_id == geo_id.get_value())
        result = session.exec(statement).first()

        if result is not None:
            return result

        raise ValueError(f"No international code found for geo_id {geo_id.get_value()}")

    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(
            f"Database error occurred while fetching international code for geo_id: {geo_id.get_value()}: {str(db_error)}")
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {str(general_exception)}")


if __name__ == "__main__":
    print(
        "This is only a library. Nothing will happen when you execute it"
    )
