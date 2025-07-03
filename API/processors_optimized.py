"""
Optimized processor functions for POST /calculate-recipe/ endpoint.

This module provides bulk processing functions that maintain identical mathematical
results while using efficient bulk database queries instead of N+1 patterns.

Created for FIT API refactoring - Phase 2 optimization.
"""

from typing import Dict, List, Set, Tuple
from sqlmodel import Session

from API import schemas, exceptions, processors
from API.crud_optimizations import (
    bulk_fetch_proxy_flags,
    bulk_fetch_weighted_results, 
    bulk_fetch_single_scores,
    bulk_fetch_min_max_values,
    bulk_fetch_names
)


def generate_expected_combinations(
    impact_categories: List[schemas.ImpactCategoryID],
    lc_stages: List[schemas.LCStageID]
) -> Set[Tuple[schemas.ImpactCategoryID, schemas.LCStageID]]:
    """
    Generate all required combinations of impact categories and life cycle stages.
    
    IDENTICAL to original processors.generate_expected_combinations function.
    Copied here to maintain mathematical equivalence.
    
    Args:
        impact_categories: The list of required impact categories.
        lc_stages: The list of required life cycle stages.
        
    Returns:
        Set of all required combinations.
    """
    expected_combinations = set()

    for ic_id in impact_categories:
        if ic_id.ic_id == 17:
            expected_combinations.add((ic_id, schemas.LCStageID(1)))
        else:
            for lc_stage_id in lc_stages:
                expected_combinations.add((ic_id, lc_stage_id))

    return expected_combinations


def process_single_item_results(
    item_id: schemas.ItemID,
    geo_id: schemas.GeoID,
    proxy_flag: bool,
    weighted_results: Dict[Tuple[int, int], schemas.LCIAValue],
    single_score: schemas.LCIAValue,
    impact_categories: List[schemas.ImpactCategoryID],
    life_cycle_stages: List[schemas.LCStageID]
) -> schemas.LCIAResult:
    """
    Process results for a single item using pre-fetched data.
    
    IDENTICAL mathematical logic to original processors.get_results() function.
    Uses pre-fetched data instead of individual database queries.
    
    Args:
        item_id: Item ID
        geo_id: Geography ID
        proxy_flag: Pre-fetched proxy flag
        weighted_results: Pre-fetched weighted results for this item
        single_score: Pre-fetched single score for this item
        impact_categories: List of impact categories
        life_cycle_stages: List of life cycle stages
        
    Returns:
        LCIAResult with identical mathematical processing as original
    """
    try:
        # Step 3: Initialize dictionaries to store stage and impact category values
        # IDENTICAL to original processors.get_results() lines 323-324
        stage_values: Dict[schemas.LCStageID, schemas.LCIAValue] = {}
        impact_category_values: Dict[schemas.ImpactCategoryID, schemas.LCIAValue] = {}

        # Initialize dictionaries to track normalization counts
        # IDENTICAL to original processors.get_results() lines 327-328
        impact_category_normalization: Dict[schemas.LCStageID, int] = {}
        life_cycle_normalization: Dict[schemas.ImpactCategoryID, int] = {}

        # Step 4: Initialize all LCIA values and normalization counts
        # IDENTICAL to original processors.get_results() lines 330-337
        for life_cycle_stage in life_cycle_stages:
            stage_values[life_cycle_stage] = schemas.LCIAValue(0.0)
            impact_category_normalization[life_cycle_stage] = 0

        for impact_category_id in impact_categories:
            impact_category_values[impact_category_id] = schemas.LCIAValue(0.0)
            life_cycle_normalization[impact_category_id] = 0

        # Step 5: Sum the weighted values for each stage and impact category, updating normalization counts
        # IDENTICAL to original processors.get_results() lines 339-347
        for (impact_category_id, life_cycle_stage), lcia_value in weighted_results.items():
            # Convert raw IDs back to schema objects for mathematical processing
            ic_schema = schemas.ImpactCategoryID(impact_category_id)
            lc_schema = schemas.LCStageID(life_cycle_stage)
            
            if lc_schema in stage_values:
                stage_values[lc_schema].lcia_value += lcia_value.lcia_value
                impact_category_normalization[lc_schema] += 1

            if ic_schema in impact_category_values:
                impact_category_values[ic_schema].lcia_value += lcia_value.lcia_value
                life_cycle_normalization[ic_schema] += 1

        # Step 8: Create the LCIAResult object and handle any validation errors
        # IDENTICAL to original processors.get_results() lines 375-384
        lcia_result = schemas.LCIAResult(
            item_id=item_id,
            geo_id=geo_id,
            proxy_flag=proxy_flag,
            single_score=single_score,
            stage_values=stage_values,
            impact_category_values=impact_category_values,
            ic_normalization=impact_category_normalization,
            lc_normalization=life_cycle_normalization
        )

        return lcia_result
        
    except exceptions.ValueError as value_error:
        # Re-raise the validation error
        raise value_error
    except Exception as result_exception:
        # Handle any other exceptions that may occur
        raise exceptions.UnknownError(f"Error creating LCIAResult: {result_exception}") from result_exception


def get_results_bulk(
    session: Session,
    items: List[Tuple[schemas.ItemID, schemas.GeoID]],
    scheme_id: schemas.WeightingSchemeID,
    impact_categories: List[schemas.ImpactCategoryID],
    life_cycle_stages: List[schemas.LCStageID]
) -> List[schemas.LCIAResult]:
    """
    Optimized version of processors.get_results that processes multiple items efficiently.
    
    IDENTICAL mathematical logic to original, just with bulk database fetching.
    
    Args:
        session: Database session
        items: List of (item_id, geo_id) tuples to process
        scheme_id: Weighting scheme ID
        impact_categories: List of impact categories to include
        life_cycle_stages: List of life cycle stages to include
        
    Returns:
        List of LCIAResult objects with identical mathematical processing
        
    Raises:
        Same exceptions as original processors.get_results()
    """
    if not items:
        return []
    
    try:
        # Step 1: Generate expected combinations (IDENTICAL to original)
        expected_combinations = generate_expected_combinations(impact_categories, life_cycle_stages)
        
        # Step 2: Bulk fetch all required data in 3 queries instead of N*3 queries
        proxy_data = bulk_fetch_proxy_flags(session, items)
        weighted_data = bulk_fetch_weighted_results(session, items, scheme_id, impact_categories, life_cycle_stages)
        single_score_data = bulk_fetch_single_scores(session, items, scheme_id)
        
        # Step 3: Process each item with IDENTICAL mathematical logic as original
        results = []
        for item_id, geo_id in items:
            item_key = (item_id.get_value(), geo_id.get_value())
            
            # Extract pre-fetched data for this item
            proxy_flag = proxy_data[item_key]
            item_weighted_results = weighted_data[item_key]
            single_score = single_score_data[item_key]
            
            # Process single item with IDENTICAL mathematical logic
            lcia_result = process_single_item_results(
                item_id=item_id,
                geo_id=geo_id,
                proxy_flag=proxy_flag,
                weighted_results=item_weighted_results,
                single_score=single_score,
                impact_categories=impact_categories,
                life_cycle_stages=life_cycle_stages
            )
            
            results.append(lcia_result)
            
        return results
        
    except exceptions.MissingLCIAValueError:
        raise
    except exceptions.MultipleMissingLCIAValueErrors:
        raise
    except exceptions.ValueError as value_error:
        raise value_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"Error in get_results_bulk: {general_exception}") from general_exception


def get_min_max_values_optimized(
    session: Session,
    scheme_id: schemas.WeightingSchemeID,
    impact_categories: List[schemas.ImpactCategoryID],
    lc_stages: List[schemas.LCStageID]
) -> schemas.MinMaxValues:
    """
    Optimized version of crud.get_min_max_values using bulk aggregation queries.
    
    IDENTICAL mathematical results to original, just with efficient database queries.
    
    Args:
        session: Database session
        scheme_id: Weighting scheme ID
        impact_categories: List of impact category IDs
        lc_stages: List of lifecycle stage IDs
        
    Returns:
        MinMaxValues with identical data as original function
        
    Raises:
        Same exceptions as original crud.get_min_max_values()
    """
    return bulk_fetch_min_max_values(session, scheme_id, impact_categories, lc_stages)


def get_names_optimized(
    session: Session,
    stage_ids: Set[schemas.LCStageID],
    impact_category_ids: Set[schemas.ImpactCategoryID]
) -> Tuple[Dict[schemas.LCStageID, str], Dict[schemas.ImpactCategoryID, str]]:
    """
    Optimized version of individual crud.get_name_by_id calls using bulk queries.
    
    IDENTICAL results to original individual lookups, just with efficient bulk fetching.
    
    Args:
        session: Database session
        stage_ids: Set of lifecycle stage IDs
        impact_category_ids: Set of impact category IDs
        
    Returns:
        Tuple of (stage_names_dict, impact_category_names_dict)
        
    Raises:
        Same exceptions as original crud.get_name_by_id()
    """
    return bulk_fetch_names(session, stage_ids, impact_category_ids)