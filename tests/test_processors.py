import pytest
from API import schemas
from API.processors import apply_grading_scheme


def test_apply_grading_scheme(valid_data):
    """
    Test the apply_grading_scheme function using valid_data to verify truncation, scaling, and preservation of LCIA values.
    """
    # Arrange
    data = valid_data
    scheme_id = schemas.WeightingSchemeID(data["scheme_ids"][0])  # Correctly initialize the schema
    min_max_values = data["min_max_values"]
    single_score_min = schemas.LCIAValue(min_max_values["single_score_min"])  # Positional initialization
    single_score_max = schemas.LCIAValue(min_max_values["single_score_max"])
    ic_mins = {schemas.ImpactCategoryID(ic_id): schemas.LCIAValue(value) for ic_id, value in min_max_values["ic_mins"].items()}
    ic_maxs = {schemas.ImpactCategoryID(ic_id): schemas.LCIAValue(value) for ic_id, value in min_max_values["ic_maxs"].items()}
    lc_mins = {schemas.LCStageID(stage_id): schemas.LCIAValue(value) for stage_id, value in min_max_values["lc_mins"].items()}
    lc_maxs = {schemas.LCStageID(stage_id): schemas.LCIAValue(value) for stage_id, value in min_max_values["lc_maxs"].items()}

    # Iterate through all items
    for item_id, geo_id, proxy_flag in zip(data["item_ids"], data["geo_ids"], data["proxy_flags"]):
        item_id_schema = schemas.ItemID(item_id)  # Positional initialization for ItemID
        geo_id_schema = schemas.GeoID(geo_id)  # Positional initialization for GeoID
        single_score = schemas.LCIAValue(data["single_scores"][(item_id, geo_id, data["scheme_ids"][0])])
        weighted_results = data["weighted_results"]

        # LCIA values for stages and impact categories from weighted_results
        stage_values = {
            schemas.LCStageID(stage_id): schemas.LCIAValue(
                weighted_results[(item_id, geo_id, data["impact_categories"][0], stage_id, data["scheme_ids"][0])]
            )
            for stage_id in data["stages"]
        }
        impact_category_values = {
            schemas.ImpactCategoryID(ic_id): schemas.LCIAValue(
                weighted_results[(item_id, geo_id, ic_id, data["stages"][0], data["scheme_ids"][0])]
            )
            for ic_id in data["impact_categories"]
        }

        # Create LCIAResult for the current item
        lcia_result = schemas.LCIAResult(
            item_id=item_id_schema,
            geo_id=geo_id_schema,
            proxy_flag=proxy_flag,
            single_score=single_score,
            stage_values=stage_values,
            impact_category_values=impact_category_values,
            ic_normalization={schemas.LCStageID(stage_id): 1 for stage_id in data["stages"]},
            lc_normalization={schemas.ImpactCategoryID(ic_id): 1 for ic_id in data["impact_categories"]},
        )

        # Prepare MinMaxValues schema
        min_max_values_schema = schemas.MinMaxValues(
            scheme_id=scheme_id,
            single_score_min=single_score_min,
            single_score_max=single_score_max,
            ic_mins=ic_mins,
            ic_maxs=ic_maxs,
            lc_mins=lc_mins,
            lc_maxs=lc_maxs,
        )

        # Act
        graded_result: schemas.GradedLCIAResult = apply_grading_scheme(
            lcia_result=lcia_result,
            min_max_values=min_max_values_schema,
        )

        # Assert
        # For single score
        if proxy_flag:
            if single_score.lcia_value < single_score_min.lcia_value:
                assert graded_result.single_score.scaled_value == 0
            elif single_score.lcia_value > single_score_max.lcia_value:
                assert graded_result.single_score.scaled_value == 1
            else:
                assert 0 <= graded_result.single_score.scaled_value <= 1
        else:
            assert 0 <= graded_result.single_score.scaled_value <= 1

        # Check that single_score lcia_value is unchanged
        assert graded_result.single_score.lcia_value == single_score.lcia_value

        # For stage values
        for stage_id, stage_value in graded_result.stage_values.items():
            original_value = stage_values[stage_id].lcia_value
            # Ensure the scaled value is correct
            if proxy_flag:
                if original_value < lc_mins[stage_id].lcia_value:
                    assert stage_value.scaled_value == 0
                elif original_value > lc_maxs[stage_id].lcia_value:
                    assert stage_value.scaled_value == 1
                else:
                    assert 0 <= stage_value.scaled_value <= 1
            else:
                assert 0 <= stage_value.scaled_value <= 1

            # Ensure the lcia_value is unchanged
            assert stage_value.lcia_value == original_value

        # For impact category values
        for ic_id, ic_value in graded_result.impact_category_values.items():
            original_value = impact_category_values[ic_id].lcia_value
            # Ensure the scaled value is correct
            if proxy_flag:
                if original_value < ic_mins[ic_id].lcia_value:
                    assert ic_value.scaled_value == 0
                elif original_value > ic_maxs[ic_id].lcia_value:
                    assert ic_value.scaled_value == 1
                else:
                    assert 0 <= ic_value.scaled_value <= 1
            else:
                assert 0 <= ic_value.scaled_value <= 1

            # Ensure the lcia_value is unchanged
            assert ic_value.lcia_value == original_value
