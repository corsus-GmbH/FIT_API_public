import math
from typing import (
    List,
    Dict, Set, Tuple,
)

from pydantic import ValidationError
from sqlmodel import Session

from API import (
    crud,
    schemas, exceptions,
)


def get_combined_grade(*scaled_lcia_values: float) -> float:
    """
    Compute the Euclidean norm of an arbitrary number of scaled LCIA values and return the combined scaled value.

    Args:
        *scaled_lcia_values (float): An arbitrary number of scaled LCIA grade values.

    Returns:
        float: The combined scaled value based on the Euclidean norm of the input values.
    """
    # Calculate the Euclidean norm of the vector formed by scaled_lcia_values
    combined_grade = math.sqrt(sum(value ** 2 for value in scaled_lcia_values)) / math.sqrt(len(scaled_lcia_values))
    return combined_grade


def log_scale(value: float, min_value: float, max_value: float, normalization: int) -> float:
    """
    Apply logarithmic scaling to an LCI value based on min and max values, ensuring all values are scaled by
    min_value + 1, and normalized by the square root of the provided normalization value.

    Args:
        value (float): The LCI value to scale.
        min_value (float): The minimum value in the range.
        max_value (float): The maximum value in the range.
        normalization (int): The normalization factor, which will adjust the scaled value by its square root.

    Returns:
        float: The logarithmically scaled value, adjusted by the square root of the normalization value.
    """

    # Adjust all values by adding 1 to ensure positive logarithmic scaling
    adjusted_value = value + 1
    adjusted_min = min_value + 1
    adjusted_max = max_value + 1

    # Compute the scaled value
    scaled_value = (math.log(adjusted_value) - math.log(adjusted_min)) / (
            math.log(adjusted_max) - math.log(adjusted_min))

    # Normalize by the square root of the normalization value
    return scaled_value / math.sqrt(normalization)


def apply_grading_scheme(
        lcia_result: schemas.LCIAResult,
        min_max_values: schemas.MinMaxValues
) -> schemas.GradedLCIAResult:
    """
    Apply a grading scheme to single scores, stage values, and impact category values based on logarithmic scaling.
    The grading is applied based on provided min and max values for scaling, and normalized using the normalization
    values for each life cycle stage and impact category.

    Args:
        lcia_result (LCIAResult): The LCIA result containing single score, stage values, and impact category values.
        min_max_values (MinMaxValues): Min/Max values for scaling each of the graded components.

    Returns:
        GradedLCIAResult: A result object with graded and scaled values for single scores, stages, and impact
        categories.
    """
    # Apply grading and scaling to the single score (no normalization for single score)
    single_score_min_value = min_max_values.single_score_min.lcia_value
    single_score_max_value = min_max_values.single_score_max.lcia_value

    scaled_single_score = log_scale(
        lcia_result.single_score.lcia_value,
        single_score_min_value,
        single_score_max_value,
        normalization=1
    )

    try:
        graded_single_score = schemas.GradedLCIAValue(
            lcia_value=lcia_result.single_score.lcia_value,
            scaled_value=scaled_single_score,
            grade=schemas.GradedLCIAValue.assign_grade(scaled_single_score)
        )
    except ValidationError as validation_error:
        raise ValueError(
            f"Validation error for single score, item_id={lcia_result.item_id}, geo_id={lcia_result.geo_id}, "
            f"value={lcia_result.single_score.lcia_value}, scaled_value={scaled_single_score}, "
            f"min_value={single_score_min_value}, max_value={single_score_max_value}. "
            f"Original error: {validation_error.errors()}"
        ) from validation_error

    # Process and grade the stage values
    graded_stages = {}
    for stage_id, stage_value in lcia_result.stage_values.items():
        stage_min_value = min_max_values.lc_mins[stage_id].lcia_value
        stage_max_value = min_max_values.lc_maxs[stage_id].lcia_value

        # Get normalization value for this stage
        normalization_value = lcia_result.ic_normalization[stage_id]

        scaled_stage_value = log_scale(
            stage_value.lcia_value, stage_min_value, stage_max_value, normalization=normalization_value
        )

        try:
            graded_stages[stage_id] = schemas.GradedLCIAValue(
                lcia_value=stage_value.lcia_value,
                scaled_value=scaled_stage_value,
                grade=schemas.GradedLCIAValue.assign_grade(scaled_stage_value)
            )
        except ValidationError as validation_error:
            raise ValueError(
                f"Validation error for stage_id={stage_id}, item_id={lcia_result.item_id}, "
                f"geo_id={lcia_result.geo_id}, value={stage_value.lcia_value}, "
                f"scaled_value={scaled_stage_value}, min_value={stage_min_value}, max_value={stage_max_value}, "
                f"normalization_value={normalization_value}. Original error: {validation_error.errors()}"
            ) from validation_error

    # Process and grade the impact categories
    graded_impact_categories = {}
    for impact_category_id, impact_category_value in lcia_result.impact_category_values.items():
        impact_category_min_value = min_max_values.ic_mins[impact_category_id].lcia_value
        impact_category_max_value = min_max_values.ic_maxs[impact_category_id].lcia_value

        # Get normalization value for this impact category
        normalization_value = lcia_result.lc_normalization[impact_category_id]

        scaled_impact_category_value = log_scale(
            impact_category_value.lcia_value, impact_category_min_value, impact_category_max_value,
            normalization=normalization_value
        )

        try:
            graded_impact_categories[impact_category_id] = schemas.GradedLCIAValue(
                lcia_value=impact_category_value.lcia_value,
                scaled_value=scaled_impact_category_value,
                grade=schemas.GradedLCIAValue.assign_grade(scaled_impact_category_value)
            )
        except ValidationError as validation_error:
            raise ValueError(
                f"Validation error for impact_category_id={impact_category_id}, item_id={lcia_result.item_id}, "
                f"geo_id={lcia_result.geo_id}, value={impact_category_value.lcia_value}, "
                f"scaled_value={scaled_impact_category_value}, min_value={impact_category_min_value}, "
                f"max_value={impact_category_max_value}, normalization_value={normalization_value}. "
                f"Original error: {validation_error.errors()}"
            ) from validation_error

    # Return the fully graded LCIA result with item_id and geo_id added to the result level
    return schemas.GradedLCIAResult(
        item_id=lcia_result.item_id,
        geo_id=lcia_result.geo_id,
        single_score=graded_single_score,
        stage_values=graded_stages,
        impact_category_values=graded_impact_categories
    )


def generate_expected_combinations(
        impact_categories: List[schemas.ImpactCategoryID],
        lc_stages: List[schemas.LCStageID]
) -> Set[Tuple[schemas.ImpactCategoryID, schemas.LCStageID]]:
    """
    Generate all required combinations of impact categories and life cycle stages.

    Args:
        impact_categories (List[schemas.ImpactCategoryID]): The list of required impact categories.
        lc_stages (List[schemas.LCStageID]): The list of required life cycle stages.

    Returns:
        Set[Tuple[schemas.ImpactCategoryID, schemas.LCStageID]]: A set of all required combinations.
    """
    expected_combinations = set()

    for ic_id in impact_categories:
        if ic_id.ic_id == 17:
            expected_combinations.add((ic_id, schemas.LCStageID(1)))
        else:
            for lc_stage_id in lc_stages:
                expected_combinations.add((ic_id, lc_stage_id))

    return expected_combinations


def get_results(
        session: Session,
        item_id: schemas.ItemID,
        geo_id: schemas.GeoID,
        scheme_id: schemas.WeightingSchemeID,
        impact_categories: List[schemas.ImpactCategoryID],
        life_cycle_stages: List[schemas.LCStageID]
) -> schemas.LCIAResult:
    """
    Get the LCIA results for the specified item, geo, and scheme, including both stage and impact category aggregation,
    and track the normalization counts for stages and impact categories.

    Args:
        session (Session): The database session.
        item_id (schemas.ItemID): The item ID.
        geo_id (schemas.GeoID): The geographical ID.
        scheme_id (schemas.WeightingSchemeID): The scheme ID.
        impact_categories (List[schemas.ImpactCategoryID]): List of impact categories to include in the result.
        life_cycle_stages (List[schemas.LCStageID]): List of life cycle stages to include in the result.

    Returns:
        schemas.LCIAResult: The aggregated LCIA result containing single score, stage values, impact category values,
                            as well as ic_normalization (number of summed categories for each stage)
                            and lc_normalization (number of summed stages for each category).

    Raises:
        exceptions.MultipleMissingLCIAValueErrors: If multiple required combinations are missing.
        exceptions.MissingLCIAValueError: If the single score is missing.
        exceptions.ValueError: If validation fails when creating the LCIAResult object.
        exceptions.UnknownError: For any other unexpected errors.
    """

    # Step 1: Generate the expected combinations
    expected_combinations = generate_expected_combinations(impact_categories, life_cycle_stages)

    # Step 2: Fetch only the expected combinations from weighted results
    try:
        weighted_results = crud.fetch_results_from_weighted_results(
            session=session,
            item_id=item_id,
            geo_id=geo_id,
            scheme_id=scheme_id,
            expected_combinations=expected_combinations
        )
    except exceptions.MissingLCIAValueError as missing_value_error:
        # If any required combination is missing, collect the errors
        missing_errors = [missing_value_error]
        raise exceptions.MultipleMissingLCIAValueErrors(missing_errors) from missing_value_error
    except exceptions.ValueError as value_error:
        raise value_error
    except Exception as general_exception:
        # Re-raise any other exceptions with additional context
        raise exceptions.UnknownError(f"Error fetching weighted results: {general_exception}") from general_exception

    # Step 3: Initialize dictionaries to store stage and impact category values
    stage_values: Dict[schemas.LCStageID, schemas.LCIAValue] = {}
    impact_category_values: Dict[schemas.ImpactCategoryID, schemas.LCIAValue] = {}

    # Initialize dictionaries to track normalization counts
    impact_category_normalization: Dict[schemas.LCStageID, int] = {}
    life_cycle_normalization: Dict[schemas.ImpactCategoryID, int] = {}

    # Step 4: Initialize all LCIA values and normalization counts
    for life_cycle_stage in life_cycle_stages:
        stage_values[life_cycle_stage] = schemas.LCIAValue(0.0)
        impact_category_normalization[life_cycle_stage] = 0

    for impact_category_id in impact_categories:
        impact_category_values[impact_category_id] = schemas.LCIAValue(0.0)
        life_cycle_normalization[impact_category_id] = 0

    # Step 5: Sum the weighted values for each stage and impact category, updating normalization counts
    for (impact_category_id, life_cycle_stage), lcia_value in weighted_results.items():
        if life_cycle_stage in stage_values:
            stage_values[life_cycle_stage].lcia_value += lcia_value.lcia_value
            impact_category_normalization[life_cycle_stage] += 1

        if impact_category_id in impact_category_values:
            impact_category_values[impact_category_id].lcia_value += lcia_value.lcia_value
            life_cycle_normalization[impact_category_id] += 1

    # Step 6: Fetch the single score
    try:
        single_score = crud.fetch_result_from_single_scores(
            session=session,
            item_id=item_id,
            geo_id=geo_id,
            scheme_id=scheme_id
        )
    except exceptions.MissingLCIAValueError as missing_value_error:
        # Raise a specific error if the single score is missing
        raise exceptions.MissingLCIAValueError(
            f"Single score missing for item_id: {item_id.get_value()}, "
            f"geo_id: {geo_id.get_value()}, scheme_id: {scheme_id.get_value()}"
        ) from missing_value_error
    except exceptions.ValueError as value_error:
        # Handle validation errors from CRUD functions
        raise value_error
    except Exception as general_exception:
        # Re-raise any other exceptions with additional context
        raise exceptions.UnknownError(f"Error fetching single score: {general_exception}") from general_exception

    # Step 7: Create the LCIAResult object and handle any validation errors
    try:
        lcia_result = schemas.LCIAResult(
            item_id=item_id,
            geo_id=geo_id,
            single_score=single_score,
            stage_values=stage_values,
            impact_category_values=impact_category_values,
            ic_normalization=impact_category_normalization,
            lc_normalization=life_cycle_normalization
        )
    except exceptions.ValueError as value_error:
        # Re-raise the validation error
        raise value_error
    except Exception as result_exception:
        # Handle any other exceptions that may occur
        raise exceptions.UnknownError(f"Error creating LCIAResult: {result_exception}") from result_exception

    # Step 8: Return the LCIAResult
    return lcia_result


def calculate_recipe(graded_lcia_results: List[schemas.GradedLCIAResult]) -> schemas.GradedLCIAResult:
    """
    Aggregates multiple graded LCI results into a single graded result by summing raw LCI values
    and computing the Euclidean norm for scaled values, individually for each stage and impact category.

    Args:
        graded_lcia_results (List[schemas.GradedLCIAResult]): A list of graded LCI results.

    Returns:
        schemas.GradedLCIAResult: The aggregated LCI result with new graded values and aggregated raw values.
    """
    total_single_scores = []
    total_single_raw_values = 0
    total_impact_category_scores = {}
    total_impact_category_raw_values = {}
    total_stage_scores = {}
    total_stage_raw_values = {}

    # Aggregate LCI values
    for result in graded_lcia_results:
        # Single score aggregation
        total_single_scores.append(result.single_score.scaled_value)
        total_single_raw_values += result.single_score.lcia_value

        # Impact category aggregation
        for category_id, graded_value in result.impact_category_values.items():
            if category_id not in total_impact_category_scores:
                total_impact_category_scores[category_id] = []
                total_impact_category_raw_values[category_id] = 0
            total_impact_category_scores[category_id].append(graded_value.scaled_value)
            total_impact_category_raw_values[category_id] += graded_value.lcia_value

        # Lifecycle stage aggregation
        for stage_id, graded_value in result.stage_values.items():
            if stage_id not in total_stage_scores:
                total_stage_scores[stage_id] = []
                total_stage_raw_values[stage_id] = 0
            total_stage_scores[stage_id].append(graded_value.scaled_value)
            total_stage_raw_values[stage_id] += graded_value.lcia_value

    # Compute Euclidean norm for single scores (scaled) and sum for raw
    combined_single_score_scaled = get_combined_grade(*total_single_scores)

    # Compute graded values and summed raw values for impact categories
    graded_impact_categories = {}
    for category_id, scores in total_impact_category_scores.items():
        combined_score_scaled = get_combined_grade(*scores)
        combined_score_raw = total_impact_category_raw_values[category_id]
        grade = schemas.GradedLCIAValue.assign_grade(combined_score_scaled)
        graded_impact_categories[category_id] = schemas.GradedLCIAValue(
            lcia_value=combined_score_raw,
            scaled_value=combined_score_scaled,
            grade=grade
        )

    # Compute graded values and summed raw values for lifecycle stages
    graded_stages = {}
    for stage_id, scores in total_stage_scores.items():
        combined_score_scaled = get_combined_grade(*scores)
        combined_score_raw = total_stage_raw_values[stage_id]
        graded_stages[stage_id] = schemas.GradedLCIAValue(
            lcia_value=combined_score_raw,
            scaled_value=combined_score_scaled,
            grade=schemas.GradedLCIAValue.assign_grade(combined_score_scaled)
        )

    # Assign grade for single score
    single_score_grade = schemas.GradedLCIAValue.assign_grade(combined_single_score_scaled)
    graded_single_score = schemas.GradedLCIAValue(
        lcia_value=total_single_raw_values,
        scaled_value=combined_single_score_scaled,
        grade=single_score_grade
    )

    # Return the new aggregated result
    return schemas.GradedLCIAResult(
        single_score=graded_single_score,
        stage_values=graded_stages,
        impact_category_values=graded_impact_categories
    )


def process_input_data(data: schemas.InputData, session: Session) -> None:
    """
    Process the input data by converting country acronyms to geo_ids for each UniqueID.
    Converts ItemCountryAcronym keys to UniqueID if necessary and resolves geo_id.
    Assumes that both item_id and geo_id must always be present.
    """
    updated_items = {}

    for key, item_amount in data.items.items():
        if isinstance(key, schemas.ItemCountryAcronym):
            # Parse the item-country_acronym string
            try:
                item_id_str, country_acronym = key.get_tuple()
            except ValueError:
                raise ValueError(
                    f"Invalid format for item_id-country_acronym: {key.item_id_country_acronym}. Expected format: "
                    f"'item_id-country_acronym'.")

            # Resolve geo_id using the country acronym
            try:
                geo_id = crud.get_geoid_by_country_acronym(session, country_acronym)
            except Exception:
                raise ValueError(f"Invalid country acronym: {country_acronym}. Could not resolve to a geo_id.")

            # Create the UniqueID with the resolved geo_id and set the item_id
            unique_id = schemas.UniqueID(
                item_id=schemas.ItemID(item_id_str),
                item_id_country_acronym=key,
                geo_id=geo_id
            )

            # Use the UniqueID as the key
            updated_items[unique_id] = item_amount

        elif isinstance(key, schemas.UniqueID):
            # No need to resolve geo_id if it is already provided
            updated_items[key] = item_amount

    # Replace the items in the input data with the updated ones (in-place modification)
    data.items = updated_items


if __name__ == "__main__":
    print(
        "This is only a library. Nothing will happen when you execute it"
    )
