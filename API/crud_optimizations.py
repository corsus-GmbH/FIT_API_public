"""
Optimized bulk database query functions for POST /calculate-recipe/ endpoint.

This module provides bulk fetching functions to replace N+1 query patterns
with efficient bulk operations while maintaining identical mathematical results.

Created for FIT API refactoring - Phase 1 optimization.
"""

from typing import Dict, List, Tuple, Set
from sqlmodel import Session, select, func
from sqlalchemy.exc import SQLAlchemyError

from API import models, schemas, exceptions


def bulk_fetch_proxy_flags(
    session: Session, 
    items: List[Tuple[schemas.ItemID, schemas.GeoID]]
) -> Dict[Tuple[int, int], bool]:
    """
    Fetch proxy flags for multiple items in a single database query.
    
    Args:
        session: Database session
        items: List of (item_id, geo_id) tuples
        
    Returns:
        Dict mapping (item_id, geo_id) -> proxy_flag
        
    Raises:
        exceptions.NameNotFoundError: If any required proxy flag is missing
        SQLAlchemyError: If database error occurs
        exceptions.UnknownError: For unexpected errors
    """
    if not items:
        return {}
        
    try:
        # Extract item_ids and geo_ids for the query
        item_ids = [item[0].get_value() for item in items]
        geo_ids = [item[1].get_value() for item in items]
        
        # Single query to fetch all proxy flags
        query = select(
            models.MetaData.item_id,
            models.MetaData.geo_id,
            models.MetaData.proxy_flag
        ).where(
            (models.MetaData.item_id.in_(item_ids)) &
            (models.MetaData.geo_id.in_(geo_ids))
        )
        
        results = session.exec(query).all()
        
        # Build result dictionary
        proxy_dict = {}
        for item_id, geo_id, proxy_flag in results:
            proxy_dict[(item_id, geo_id)] = proxy_flag
            
        # Verify all requested items were found
        requested_keys = {(item[0].get_value(), item[1].get_value()) for item in items}
        found_keys = set(proxy_dict.keys())
        missing_keys = requested_keys - found_keys
        
        if missing_keys:
            missing_items = [f"item_id:{k[0]}, geo_id:{k[1]}" for k in missing_keys]
            raise exceptions.NameNotFoundError(
                "Proxy flags", "item_id and geo_id combinations", ", ".join(missing_items)
            )
            
        return proxy_dict
        
    except exceptions.NameNotFoundError:
        # Re-raise our specific exceptions
        raise
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in bulk_fetch_proxy_flags: {db_error}") from db_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"Error in bulk_fetch_proxy_flags: {general_exception}") from general_exception


def bulk_fetch_weighted_results(
    session: Session,
    items: List[Tuple[schemas.ItemID, schemas.GeoID]],
    scheme_id: schemas.WeightingSchemeID,
    impact_categories: List[schemas.ImpactCategoryID],
    life_cycle_stages: List[schemas.LCStageID]
) -> Dict[Tuple[int, int], Dict[Tuple[int, int], schemas.LCIAValue]]:
    """
    Fetch weighted results for multiple items in a single database query.
    
    Args:
        session: Database session
        items: List of (item_id, geo_id) tuples
        scheme_id: Weighting scheme ID
        impact_categories: List of impact category IDs
        life_cycle_stages: List of life cycle stage IDs
        
    Returns:
        Dict mapping (item_id, geo_id) -> {(ic_id, lc_stage_id) -> LCIAValue}
        
    Raises:
        exceptions.MissingLCIAValueError: If required combinations are missing
        SQLAlchemyError: If database error occurs
        exceptions.UnknownError: For unexpected errors
    """
    if not items:
        return {}
        
    try:
        # Extract values for query
        item_ids = [item[0].get_value() for item in items]
        geo_ids = [item[1].get_value() for item in items]
        ic_ids = [ic.get_value() for ic in impact_categories]
        lc_stage_ids = [lc.get_value() for lc in life_cycle_stages]
        
        # Single bulk query for all weighted results
        query = select(
            models.WeightedResults.item_id,
            models.WeightedResults.geo_id,
            models.WeightedResults.ic_id,
            models.WeightedResults.lc_stage_id,
            models.WeightedResults.weighted_value
        ).where(
            (models.WeightedResults.item_id.in_(item_ids)) &
            (models.WeightedResults.geo_id.in_(geo_ids)) &
            (models.WeightedResults.scheme_id == scheme_id.get_value()) &
            (models.WeightedResults.ic_id.in_(ic_ids)) &
            (models.WeightedResults.lc_stage_id.in_(lc_stage_ids))
        )
        
        results = session.exec(query).all()
        
        # Organize results by item
        weighted_dict = {}
        for item_id, geo_id, ic_id, lc_stage_id, weighted_value in results:
            item_key = (item_id, geo_id)
            if item_key not in weighted_dict:
                weighted_dict[item_key] = {}
            
            combination_key = (ic_id, lc_stage_id)
            weighted_dict[item_key][combination_key] = schemas.LCIAValue(weighted_value)
            
        # Generate the same expected combinations as the original code
        # This properly handles IC 17 only having stage 1
        expected_combinations = set()
        for ic in impact_categories:
            if ic.get_value() == 17:
                expected_combinations.add((ic.get_value(), 1))  # Only stage 1 for IC 17
            else:
                for lc in life_cycle_stages:
                    expected_combinations.add((ic.get_value(), lc.get_value()))
        
        missing_errors = []
        for item in items:
            item_key = (item[0].get_value(), item[1].get_value())
            item_results = weighted_dict.get(item_key, {})
            found_combinations = set(item_results.keys())
            missing_combinations = expected_combinations - found_combinations
            
            if missing_combinations:
                for ic_id, lc_id in missing_combinations:
                    error_msg = (f"Missing weighted result for item_id: {item_key[0]}, "
                               f"geo_id: {item_key[1]}, ic_id: {ic_id}, lc_stage_id: {lc_id}, "
                               f"scheme_id: {scheme_id.get_value()}")
                    missing_errors.append(exceptions.MissingLCIAValueError(
                        item_id=str(item_key[0]), 
                        geo_id=item_key[1], 
                        stage_id=lc_id, 
                        ic_id=ic_id,
                        table_name="weightedresults",
                        message=error_msg
                    ))
        
        if missing_errors:
            raise exceptions.MultipleMissingLCIAValueErrors(missing_errors)
            
        return weighted_dict
        
    except exceptions.MissingLCIAValueError:
        raise
    except exceptions.MultipleMissingLCIAValueErrors:
        raise
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in bulk_fetch_weighted_results: {db_error}") from db_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"Error in bulk_fetch_weighted_results: {general_exception}") from general_exception


def bulk_fetch_single_scores(
    session: Session,
    items: List[Tuple[schemas.ItemID, schemas.GeoID]],
    scheme_id: schemas.WeightingSchemeID
) -> Dict[Tuple[int, int], schemas.LCIAValue]:
    """
    Fetch single scores for multiple items in a single database query.
    
    Args:
        session: Database session
        items: List of (item_id, geo_id) tuples
        scheme_id: Weighting scheme ID
        
    Returns:
        Dict mapping (item_id, geo_id) -> LCIAValue
        
    Raises:
        exceptions.MissingLCIAValueError: If required single scores are missing
        SQLAlchemyError: If database error occurs
        exceptions.UnknownError: For unexpected errors
    """
    if not items:
        return {}
        
    try:
        # Extract values for query
        item_ids = [item[0].get_value() for item in items]
        geo_ids = [item[1].get_value() for item in items]
        
        # Single bulk query for all single scores
        query = select(
            models.SingleScores.item_id,
            models.SingleScores.geo_id,
            models.SingleScores.single_score
        ).where(
            (models.SingleScores.item_id.in_(item_ids)) &
            (models.SingleScores.geo_id.in_(geo_ids)) &
            (models.SingleScores.scheme_id == scheme_id.get_value())
        )
        
        results = session.exec(query).all()
        
        # Build result dictionary
        score_dict = {}
        for item_id, geo_id, single_score in results:
            score_dict[(item_id, geo_id)] = schemas.LCIAValue(single_score)
            
        # Verify all requested items were found
        requested_keys = {(item[0].get_value(), item[1].get_value()) for item in items}
        found_keys = set(score_dict.keys())
        missing_keys = requested_keys - found_keys
        
        if missing_keys:
            missing_errors = []
            for item_id, geo_id in missing_keys:
                error_msg = (f"Single score missing for item_id: {item_id}, "
                           f"geo_id: {geo_id}, scheme_id: {scheme_id.get_value()}")
                missing_errors.append(exceptions.MissingLCIAValueError(
                    item_id=str(item_id), 
                    geo_id=geo_id, 
                    table_name="singlescores",
                    message=error_msg
                ))
            raise exceptions.MultipleMissingLCIAValueErrors(missing_errors)
            
        return score_dict
        
    except exceptions.MissingLCIAValueError:
        raise
    except exceptions.MultipleMissingLCIAValueErrors:
        raise
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in bulk_fetch_single_scores: {db_error}") from db_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"Error in bulk_fetch_single_scores: {general_exception}") from general_exception


def bulk_fetch_min_max_values(
    session: Session,
    scheme_id: schemas.WeightingSchemeID,
    impact_category_ids: List[schemas.ImpactCategoryID],
    lc_stage_ids: List[schemas.LCStageID]
) -> schemas.MinMaxValues:
    """
    Fetch min/max values for all impact categories and lifecycle stages in optimized queries.
    
    Replaces individual per-category and per-stage queries with efficient aggregation.
    
    Args:
        session: Database session
        scheme_id: Weighting scheme ID
        impact_category_ids: List of impact category IDs
        lc_stage_ids: List of lifecycle stage IDs
        
    Returns:
        MinMaxValues schema with all min/max data
        
    Raises:
        SQLAlchemyError: If database error occurs
        exceptions.UnknownError: For unexpected errors
    """
    try:
        # Extract values for queries
        ic_ids = [ic.get_value() for ic in impact_category_ids]
        lc_ids = [lc.get_value() for lc in lc_stage_ids]
        
        # Single aggregation query for impact category min/max values
        ic_query = select(
            models.WeightedResults.ic_id,
            func.min(models.WeightedResults.weighted_value).label('min_val'),
            func.max(models.WeightedResults.weighted_value).label('max_val')
        ).join(
            models.MetaData, 
            models.WeightedResults.item_id == models.MetaData.item_id
        ).where(
            (models.WeightedResults.scheme_id == scheme_id.get_value()) &
            (models.MetaData.proxy_flag == False) &
            (models.WeightedResults.ic_id.in_(ic_ids))
        ).group_by(
            models.WeightedResults.ic_id
        )
        
        ic_results = session.exec(ic_query).all()
        
        # Single aggregation query for lifecycle stage min/max values
        lc_query = select(
            models.WeightedResults.lc_stage_id,
            func.min(models.WeightedResults.weighted_value).label('min_val'),
            func.max(models.WeightedResults.weighted_value).label('max_val')
        ).join(
            models.MetaData,
            models.WeightedResults.item_id == models.MetaData.item_id
        ).where(
            (models.WeightedResults.scheme_id == scheme_id.get_value()) &
            (models.MetaData.proxy_flag == False) &
            (models.WeightedResults.lc_stage_id.in_(lc_ids))
        ).group_by(
            models.WeightedResults.lc_stage_id
        )
        
        lc_results = session.exec(lc_query).all()
        
        # Build min/max dictionaries in the correct format
        ic_mins = {}
        ic_maxs = {}
        for ic_id, min_val, max_val in ic_results:
            ic_mins[schemas.ImpactCategoryID(ic_id)] = schemas.LCIAValue(min_val if min_val is not None else 0.0)
            ic_maxs[schemas.ImpactCategoryID(ic_id)] = schemas.LCIAValue(max_val if max_val is not None else 0.0)
            
        lc_mins = {}
        lc_maxs = {}
        for lc_id, min_val, max_val in lc_results:
            lc_mins[schemas.LCStageID(lc_id)] = schemas.LCIAValue(min_val if min_val is not None else 0.0)
            lc_maxs[schemas.LCStageID(lc_id)] = schemas.LCIAValue(max_val if max_val is not None else 0.0)
        
        # We need to get single score min/max as well to match the original schema
        # For now, let's add placeholder values - this should be added properly
        single_score_query = select(
            func.max(models.SingleScores.single_score).label('max_val'),
            func.min(models.SingleScores.single_score).label('min_val')
        ).join(
            models.MetaData,
            models.SingleScores.item_id == models.MetaData.item_id
        ).where(
            (models.SingleScores.scheme_id == scheme_id.get_value()) &
            (models.MetaData.proxy_flag == False)
        )
        
        single_score_result = session.exec(single_score_query).first()
        single_score_max = single_score_result[0] if single_score_result and single_score_result[0] is not None else 0.0
        single_score_min = single_score_result[1] if single_score_result and single_score_result[1] is not None else 0.0
            
        return schemas.MinMaxValues(
            scheme_id=scheme_id,
            single_score_max=schemas.LCIAValue(single_score_max),
            single_score_min=schemas.LCIAValue(single_score_min),
            ic_mins=ic_mins,
            ic_maxs=ic_maxs,
            lc_mins=lc_mins,
            lc_maxs=lc_maxs
        )
        
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in bulk_fetch_min_max_values: {db_error}") from db_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"Error in bulk_fetch_min_max_values: {general_exception}") from general_exception


def bulk_fetch_names(
    session: Session,
    stage_ids: Set[schemas.LCStageID],
    impact_category_ids: Set[schemas.ImpactCategoryID]
) -> Tuple[Dict[schemas.LCStageID, str], Dict[schemas.ImpactCategoryID, str]]:
    """
    Fetch stage and impact category names in bulk queries.
    
    Replaces individual name lookups with efficient bulk fetching.
    
    Args:
        session: Database session
        stage_ids: Set of lifecycle stage IDs
        impact_category_ids: Set of impact category IDs
        
    Returns:
        Tuple of (stage_names_dict, impact_category_names_dict)
        
    Raises:
        SQLAlchemyError: If database error occurs
        exceptions.UnknownError: For unexpected errors
    """
    try:
        stage_names = {}
        ic_names = {}
        
        # Bulk fetch stage names if any requested
        if stage_ids:
            stage_id_values = [stage_id.get_value() for stage_id in stage_ids]
            stage_query = select(
                models.LifeCycleStages.lc_stage_id,
                models.LifeCycleStages.lc_name
            ).where(
                models.LifeCycleStages.lc_stage_id.in_(stage_id_values)
            )
            
            stage_results = session.exec(stage_query).all()
            for lc_stage_id, lc_name in stage_results:
                stage_names[schemas.LCStageID(lc_stage_id)] = lc_name
                
        # Bulk fetch impact category names if any requested
        if impact_category_ids:
            ic_id_values = [ic_id.get_value() for ic_id in impact_category_ids]
            ic_query = select(
                models.ImpactCategories.ic_id,
                models.ImpactCategories.ic_name
            ).where(
                models.ImpactCategories.ic_id.in_(ic_id_values)
            )
            
            ic_results = session.exec(ic_query).all()
            for ic_id, ic_name in ic_results:
                ic_names[schemas.ImpactCategoryID(ic_id)] = ic_name
                
        return stage_names, ic_names
        
    except SQLAlchemyError as db_error:
        raise SQLAlchemyError(f"Database error in bulk_fetch_names: {db_error}") from db_error
    except Exception as general_exception:
        raise exceptions.UnknownError(f"Error in bulk_fetch_names: {general_exception}") from general_exception