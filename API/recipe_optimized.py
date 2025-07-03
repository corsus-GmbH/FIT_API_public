"""
Optimized endpoint implementation for POST /calculate-recipe/.

This module provides an optimized version of the calculate_recipe endpoint
that uses bulk database queries while maintaining identical mathematical results.

Created for FIT API refactoring - Phase 3 optimization.
"""

from fastapi import Depends
from sqlmodel import Session
from typing import Dict

from API import schemas, processors, crud, exceptions, dependencies
from API.processors_optimized import (
    get_results_bulk,
    get_min_max_values_optimized,
    get_names_optimized
)


async def calculate_recipe_optimized(
    data: schemas.InputData,
    session: Session = Depends(dependencies._get_db_session),
) -> schemas.OutputData:
    """
    Optimized version of calculate_recipe endpoint using bulk database queries.
    
    IDENTICAL mathematical logic and output to original endpoint.
    Optimizes database access patterns from N+1 queries to bulk operations.
    
    Performance improvements:
    - Bulk fetch proxy flags (N queries -> 1 query)
    - Bulk fetch weighted results (N queries -> 1 query)  
    - Bulk fetch single scores (N queries -> 1 query)
    - Bulk fetch min/max values (~12 queries -> 2 queries)
    - Bulk fetch names (~12 queries -> 2 queries)
    
    Args:
        data: Input data with items and weighting scheme
        session: Database session
        
    Returns:
        OutputData with identical structure and values as original endpoint
        
    Raises:
        Same exceptions as original calculate_recipe endpoint
    """
    try:
        # IDENTICAL input processing to original (main.py lines 442-450)
        processors.process_input_data(data, session)

        # Fetch the corresponding weighting scheme name or ID if necessary
        if not data.weighting_scheme_name and data.weighting_scheme_id:
            data.weighting_scheme_name = crud.get_name_by_id(session, data.weighting_scheme_id)

        if not data.weighting_scheme_id and data.weighting_scheme_name:
            data.weighting_scheme_id = crud.get_scheme_id_by_weight_string(session, data.weighting_scheme_name)

        # IDENTICAL setup to original (main.py lines 452-460)
        impact_category_weights = crud.get_ic_weights_by_scheme_id(session, data.weighting_scheme_id)
        impact_categories = list(impact_category_weights.weights.keys())
        lc_stages = [
            schemas.LCStageID(1),
            schemas.LCStageID(2),
            schemas.LCStageID(4),
            schemas.LCStageID(5)
        ]

        # OPTIMIZATION: Bulk fetch all item data instead of N+1 queries
        # Original: N individual queries for each item (lines 465-479)
        # Optimized: Single bulk operation for all items
        items_list = [(unique_id.item_id, unique_id.geo_id) for unique_id in data.items.keys()]
        item_results = get_results_bulk(
            session=session,
            items=items_list,
            scheme_id=data.weighting_scheme_id,
            impact_categories=impact_categories,
            life_cycle_stages=lc_stages
        )

        # OPTIMIZATION: Bulk fetch min/max values instead of individual queries
        # Original: ~12 individual queries (line 482)
        # Optimized: 2 aggregation queries
        min_max_values = get_min_max_values_optimized(session, data.weighting_scheme_id, impact_categories, lc_stages)

        # IDENTICAL mathematical processing to original (main.py lines 484-489)
        graded_item_results = [processors.apply_grading_scheme(item_result, min_max_values) for item_result in item_results]
        recipe_scores = processors.calculate_recipe(graded_item_results)

        # IDENTICAL collection logic to original (main.py lines 491-502)
        stage_ids = set()
        impact_category_ids = set()

        # Collect from recipe scores
        stage_ids.update(recipe_scores.stage_values.keys())
        impact_category_ids.update(recipe_scores.impact_category_values.keys())

        # Collect from graded LCIA results for all items
        for item_result in graded_item_results:
            stage_ids.update(item_result.stage_values.keys())
            impact_category_ids.update(item_result.impact_category_values.keys())

        # OPTIMIZATION: Bulk fetch names instead of individual queries
        # Original: ~12 individual queries (lines 505-506)
        # Optimized: 2 bulk queries
        stage_names, impact_category_names = get_names_optimized(session, stage_ids, impact_category_ids)

        # Build proxy_flags dictionary from results (maintaining original format)
        proxy_flags = {}
        for i, unique_id in enumerate(data.items.keys()):
            proxy_flags[unique_id] = item_results[i].proxy_flag

        # IDENTICAL output preparation to original (main.py lines 509-516)
        output_data = schemas.OutputData(
            input_data=data,
            graded_lcia_results=graded_item_results,
            recipe_scores=recipe_scores,
            proxy_flags=proxy_flags,
            stage_names=stage_names,
            impact_category_names=impact_category_names
        )

        return output_data

    # IDENTICAL exception handling to original (lines 520+)
    except exceptions.InvalidItemCountryAcronymFormatError as custom_error:
        raise custom_error
    except exceptions.MissingLCIAValueError as missing_lcia_error:
        raise missing_lcia_error
    except exceptions.MultipleMissingLCIAValueErrors as multiple_missing_errors:
        raise multiple_missing_errors
    except exceptions.NameNotFoundError as name_not_found_error:
        raise name_not_found_error
    except exceptions.ValueError as value_error:
        raise value_error
    except exceptions.UnknownError as unknown_error:
        raise unknown_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"An unexpected error occurred: {general_exception}") from general_exception


# For easy integration, we can also create a function that patches the original endpoint
def get_optimized_calculate_recipe_function():
    """
    Returns the optimized calculate_recipe function for easy integration.
    
    This allows replacing the original endpoint with:
    app.post("/calculate-recipe/")(calculate_recipe_optimized)
    """
    return calculate_recipe_optimized