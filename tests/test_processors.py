from sqlmodel import select

from API import (
    processors,
    schemas,
    crud,
)
import pytest

from .conftest import (
    create_normalized_lcia_values,
    populate_normalized_lcia_values,
)




@pytest.mark.usefixtures("valid_data")
def test_apply_grading_scheme(test_db, valid_data):
    # Retrieve test parameters
    item_id = schemas.ItemID(item_id=valid_data["item_ids"][0])
    geo_id = schemas.GeoID(geo_id=valid_data["geo_ids"][0])
    scheme_id = schemas.WeightingSchemeID(scheme_id=valid_data["scheme_ids"][0])
    stage_id = schemas.LCStageID(lc_stage_id=valid_data["stages"][0])
    impact_category_ids = [schemas.ImpactCategoryID(ic_id=ic_id) for ic_id in valid_data["impact_categories"]]

    # Fetch the LCIAResult from the database
    lci_result = crud.fetch_results(
        session=test_db,
        item_id=item_id,
        geo_id=geo_id,
        scheme_id=scheme_id,
        stages=[stage_id],
        impact_categories=impact_category_ids,
    )

    # Extract min/max values from the test database
    min_max_values = crud.get_min_max_values(
        session=test_db,
        scheme_id=scheme_id,
        impact_category_ids=impact_category_ids,
    )

    # Apply the grading scheme
    graded_result = processors.apply_grading_scheme(lci_result, min_max_values)

    # Assertions for single score
    assert graded_result.single_score.lcia_value == lci_result.single_score.lcia_value, ("Single score LCI value "
                                                                                         "mismatch")
    assert 0 <= graded_result.single_score.scaled_value <= 1, "Single score scaled value should be between 0 and 1"
    assert graded_result.single_score.grade in ['A', 'B', 'C', 'D', 'F'], "Single score grade mismatch"

    # Assertions for impact categories
    for ic_id, ic_value in lci_result.impact_category_values.items():
        graded_ic_value = graded_result.impact_category_values[ic_id]
        assert graded_ic_value.lcia_value == ic_value.lcia_value, f"Impact category {ic_id.ic_id} LCI value mismatch"
        assert 0 <= graded_ic_value.scaled_value <= 1, f"Impact category {ic_id.ic_id} scaled value should be between 0 and 1"
        assert graded_ic_value.grade in ['A', 'B', 'C', 'D', 'F'], f"Impact category {ic_id.ic_id} grade mismatch"


@pytest.mark.usefixtures("valid_data")
def test_calculate_recipe_with_db(test_db, valid_data):
    """
    Test to ensure that the recipe calculation aggregates multiple graded LCI results correctly
    using data from the test_db.
    """
    # Define scheme ID and impact category IDs from valid_data
    scheme_id = schemas.WeightingSchemeID(scheme_id=valid_data["scheme_ids"][0])
    impact_category_ids = [schemas.ImpactCategoryID(ic_id=ic_id) for ic_id in valid_data["impact_categories"]]

    # Fetch min and max values for grading
    min_max_values = crud.get_min_max_values(
        session=test_db,
        scheme_id=scheme_id,
        impact_category_ids=impact_category_ids
    )

    # Retrieve LCI results from the database
    lci_result_1 = crud.fetch_results(
        session=test_db,
        item_id=schemas.ItemID(item_id=valid_data["item_ids"][0]),
        geo_id=schemas.GeoID(geo_id=valid_data["geo_ids"][0]),
        scheme_id=scheme_id,
        stages=[schemas.LCStageID(lc_stage_id=valid_data["stages"][0])],
        impact_categories=impact_category_ids
    )

    lci_result_2 = crud.fetch_results(
        session=test_db,
        item_id=schemas.ItemID(item_id=valid_data["item_ids"][1]),
        geo_id=schemas.GeoID(geo_id=valid_data["geo_ids"][1]),
        scheme_id=scheme_id,
        stages=[schemas.LCStageID(lc_stage_id=valid_data["stages"][0])],
        impact_categories=impact_category_ids
    )

    # Apply grading to each LCI result
    graded_result_1 = processors.apply_grading_scheme(lci_result_1, min_max_values)
    graded_result_2 = processors.apply_grading_scheme(lci_result_2, min_max_values)

    # List of graded results to pass to the recipe calculation
    graded_lci_results = [graded_result_1, graded_result_2]

    # Call the calculate_recipe function
    aggregated_result = processors.calculate_recipe(graded_lci_results)

    # Expected values
    expected_single_score_value = lci_result_1.single_score.lcia_value + lci_result_2.single_score.lcia_value
    expected_stage_value_1 = lci_result_1.stage_values[
                                 schemas.LCStageID(lc_stage_id=valid_data["stages"][0])].lcia_value + \
                             lci_result_2.stage_values[
                                 schemas.LCStageID(lc_stage_id=valid_data["stages"][0])].lcia_value

    # Assert the aggregated result matches the expected sum of single scores
    assert aggregated_result.single_score.lcia_value == expected_single_score_value, \
        "Single score LCI value does not match expected sum"

    # Assert the stage values are summed correctly
    assert (aggregated_result.stage_values[schemas.LCStageID(lc_stage_id=valid_data["stages"][0])].lcia_value ==
            expected_stage_value_1), \
        "Stage LCI value does not match expected sum"

    # Check scaled values and grades
    assert 0 <= aggregated_result.single_score.scaled_value <= 1, \
        "Single score scaled value out of expected range"
    assert aggregated_result.single_score.grade in ['A', 'B', 'C', 'D', 'F'], \
        "Single score grade is invalid"


def test_format_output_data(test_db, valid_data):
    # Extract test data
    item_ids = [schemas.ItemID(item_id=id) for id in valid_data["item_ids"]]
    geo_ids = [schemas.GeoID(geo_id=id) for id in valid_data["geo_ids"]]

    # Simulate graded LCIA results for two items
    graded_lcia_results = [
        schemas.GradedLCIAResult(
            item_id=item_ids[0],
            geo_id=geo_ids[0],
            single_score=schemas.GradedLCIAValue(lcia_value=50.0, scaled_value=0.25, grade="B"),
            stage_values={
                schemas.LCStageID(lc_stage_id=1): schemas.GradedLCIAValue(lcia_value=20.0, scaled_value=0.2, grade="A"),
                schemas.LCStageID(lc_stage_id=2): schemas.GradedLCIAValue(lcia_value=30.0, scaled_value=0.3, grade="B")
            },
            impact_category_values={
                schemas.ImpactCategoryID(ic_id=1): schemas.GradedLCIAValue(lcia_value=10.0, scaled_value=0.1,
                                                                           grade="A"),
                schemas.ImpactCategoryID(ic_id=2): schemas.GradedLCIAValue(lcia_value=15.0, scaled_value=0.15,
                                                                           grade="A")
            }
        ),
        schemas.GradedLCIAResult(
            item_id=item_ids[1],
            geo_id=geo_ids[1],
            single_score=schemas.GradedLCIAValue(lcia_value=60.0, scaled_value=0.35, grade="C"),
            stage_values={
                schemas.LCStageID(lc_stage_id=1): schemas.GradedLCIAValue(lcia_value=25.0, scaled_value=0.25,
                                                                          grade="B"),
                schemas.LCStageID(lc_stage_id=2): schemas.GradedLCIAValue(lcia_value=35.0, scaled_value=0.35, grade="B")
            },
            impact_category_values={
                schemas.ImpactCategoryID(ic_id=1): schemas.GradedLCIAValue(lcia_value=12.0, scaled_value=0.12,
                                                                           grade="A"),
                schemas.ImpactCategoryID(ic_id=2): schemas.GradedLCIAValue(lcia_value=18.0, scaled_value=0.18,
                                                                           grade="A")
            }
        )
    ]

    # Simulate the recipe scores as the combined result
    recipe_scores = schemas.GradedLCIAResult(
        single_score=schemas.GradedLCIAValue(lcia_value=110.0, scaled_value=0.30, grade="B"),
        stage_values={
            schemas.LCStageID(lc_stage_id=1): schemas.GradedLCIAValue(lcia_value=45.0, scaled_value=0.225, grade="B"),
            schemas.LCStageID(lc_stage_id=2): schemas.GradedLCIAValue(lcia_value=65.0, scaled_value=0.325, grade="B")
        },
        impact_category_values={
            schemas.ImpactCategoryID(ic_id=1): schemas.GradedLCIAValue(lcia_value=22.0, scaled_value=0.11, grade="A"),
            schemas.ImpactCategoryID(ic_id=2): schemas.GradedLCIAValue(lcia_value=33.0, scaled_value=0.165, grade="A")
        }
    )

    # Simulate input data using the IDs and weights
    input_data = schemas.InputData(
        items={
            schemas.UniqueID(item_id=item_ids[0].item_id, geo_id=geo_ids[0].geo_id): 0.5,
            schemas.UniqueID(item_id=item_ids[1].item_id, geo_id=geo_ids[1].geo_id): 0.5,
        },
        weighting_scheme_name="ef31_r0510"
    )

    # Run the function
    formatted_output = processors.format_output_data(test_db, input_data, graded_lcia_results, recipe_scores)

    # Validate the structure and content of the output
    output_dict = formatted_output.model_dump()
    print(output_dict)

    # Check if recipe_info exists in the output
    assert "recipe_info" in output_dict
    assert "Single Score" in output_dict["recipe_info"]
    assert "Items" in output_dict["recipe_info"]
    assert "Stages" in output_dict["recipe_info"]
    assert "Impact Categories" in output_dict["recipe_info"]

    # Check if item results exist in the output
    assert "item_results" in output_dict
    assert len(output_dict["item_results"]) == 2  # We have two items

    # Validate specific values for single score
    assert output_dict["recipe_info"]["Single Score"]["lcia_value"] == 110.0
    assert output_dict["recipe_info"]["Single Score"]["grade"] == "B"
    assert output_dict["recipe_info"]["Single Score"]["scaled_value"] == 0.30

    # Verify item names and amounts in the recipe info
    for item_key, amount in output_dict["recipe_info"]["Items"].items():
        assert amount == 0.5  # Each item has an amount of 0.5

    # Verify stage and impact category names
    for stage_name, stage_value in output_dict["recipe_info"]["Stages"].items():
        assert isinstance(stage_name, str)
        assert "lcia_value" in stage_value

    for ic_name, ic_value in output_dict["recipe_info"]["Impact Categories"].items():
        assert isinstance(ic_name, str)
        assert "lcia_value" in ic_value


if __name__ == "__main__":
    import sys

    pytest.main(
        ["-s", sys.argv[0]]
    )
