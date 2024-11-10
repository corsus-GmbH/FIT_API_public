# test_crud.py
from typing import List

import pytest
from sqlmodel import select,Session

from API import (
    models,
    crud,
    schemas,
    exceptions,
    )



def test_get_min_max_values_excludes_proxies_single_scores(test_db, valid_data):
    """
    Test `get_min_max_values` to ensure it excludes items with `proxy_flag=True`
    for single score calculations.
    """
    session = test_db

    # Prepare test inputs
    scheme_id = schemas.WeightingSchemeID(1)

    # Filter valid_data to simulate expected results for single scores
    non_proxy_item_ids = [
        item_id for item_id, is_proxy in zip(valid_data["item_ids"], valid_data["proxy_flags"]) if not is_proxy
    ]

    # Calculate expected single score min and max for non-proxy items
    relevant_single_scores = [
        value
        for (item_id, geo_id, scheme), value in valid_data["single_scores"].items()
        if item_id in non_proxy_item_ids and scheme == scheme_id.scheme_id
    ]
    expected_single_score_max = max(relevant_single_scores) if relevant_single_scores else None
    expected_single_score_min = min(relevant_single_scores) if relevant_single_scores else None

    # Call the function
    result = crud.get_min_max_values(
        session=session,
        scheme_id=scheme_id,
        impact_category_ids=[],
        lc_stage_ids=[],
    )

    # Assertions for Single Scores
    assert result.single_score_max.lcia_value == expected_single_score_max, (
        f"Expected max single score to be {expected_single_score_max}, "
        f"but got {result.single_score_max.lcia_value}."
    )
    assert result.single_score_min.lcia_value == expected_single_score_min, (
        f"Expected min single score to be {expected_single_score_min}, "
        f"but got {result.single_score_min.lcia_value}."
    )


@pytest.mark.usefixtures("valid_data")
def test_get_all_item_ids(test_db, valid_data):
    """
    Test to ensure all item IDs from the MetaData table are correctly retrieved.
    """
    expected_item_ids = valid_data["item_ids"]  # Fetch expected item IDs from the valid_data fixture
    actual_item_ids = crud.get_all_items_info(test_db)
    assert sorted(actual_item_ids) == sorted(
        expected_item_ids
        ), "The retrieved item IDs should match the expected values"


def test_retrieve_all_data(test_db, valid_data):
    """
    Test to ensure that all data can be retrieved correctly from the test_db using valid data setup.
    """
    # Test retrieval of item IDs
    expected_item_ids = valid_data["item_ids"]
    actual_item_ids = crud.get_all_items_info(test_db)
    assert sorted(actual_item_ids) == sorted(expected_item_ids), "Mismatch in retrieved item IDs."

    # Test normalized LCIA values for one item, all stages, all impact categories, and one geo ID
    item_id = valid_data["item_ids"][0]
    geo_id = valid_data["geo_ids"][0]

    for stage_id in valid_data["stages"]:
        for ic_id in valid_data["impact_categories"]:
            key = (item_id, geo_id, stage_id, ic_id)
            try:
                # Test for successful data retrieval
                lcia_value = crud.get_lci_by_key_stage_category(
                    session=test_db,
                    item_id=schemas.ItemID(item_id=item_id),
                    stage_id=schemas.LCStageID(lc_stage_id=stage_id),
                    impact_category_id=schemas.ImpactCategoryID(ic_id=ic_id),
                    geo_id=schemas.GeoID(geo_id)
                    )
                # Check if the key exists in the valid_data dictionary
                if key not in valid_data["normalized_lcias"]:
                    pytest.fail(f"Normalized LCIA values missing for {key}")

                expected_value = valid_data["normalized_lcias"][key]['normalized_lcia_value']
                assert lcia_value.lcia_value == expected_value, f"Incorrect LCI value for {key}"
            except Exception as e:
                print(f"Error retrieving data for {key}:", str(e))
                pytest.fail(f"Unexpected error for {key}: {str(e)}")


def test_get_name_by_id(
        test_db
        ):
    # Test retrieval for various types of IDs
    stage_id = schemas.LCStageID(
        lc_stage_id=1
        )
    impact_id = schemas.ImpactCategoryID(
        ic_id=1
        )
    geo_id = schemas.GeoID(
        geo_id=1
        )
    item_id = schemas.ItemID(
        item_id="1029_1"
        )
    group_id = schemas.GroupID(
        group_id=1
        )
    subgroup_id = schemas.SubgroupID(
        subgroup_id=1
        )

    # Assertions to ensure correct data retrieval
    assert isinstance(
        crud.get_name_by_id(
            test_db,
            stage_id
            ),
        str
        ), "Failed to fetch data for LCStageID"
    assert isinstance(
        crud.get_name_by_id(
            test_db,
            impact_id
            ),
        str
        ), "Failed to fetch data for ImpactCategoryID"
    assert isinstance(
        crud.get_name_by_id(
            test_db,
            geo_id
            ),
        str
        ), "Failed to fetch data for GeoID"
    assert isinstance(
        crud.get_name_by_id(
            test_db,
            item_id
            ),
        str
        ), "Failed to fetch data for ItemID"
    assert isinstance(
        crud.get_name_by_id(
            test_db,
            group_id
            ),
        str
        ), "Failed to fetch data for GroupID"
    assert isinstance(
        crud.get_name_by_id(
            test_db,
            subgroup_id
            ),
        str
        ), "Failed to fetch data for SubgroupID"


def test_get_scheme_id_by_weight_string(test_db, valid_data):
    # Testing successful retrieval
    valid_scheme_name = valid_data["weighting_names"][0]  # Using the first valid scheme name
    valid_weights = schemas.WeightingSchemeName(ic_weights=valid_scheme_name)

    scheme_id = crud.get_scheme_id_by_weight_string(test_db, valid_weights)
    #TODO make this dynamic
    expected_scheme_id = 1
    assert isinstance(scheme_id, schemas.WeightingSchemeID), "Should return a Pydantic instance of SchemeID"
    assert scheme_id.scheme_id == expected_scheme_id, f"Should fetch correct ID for valid weight string '{valid_scheme_name}'"

    # Testing retrieval failure
    invalid_weights = schemas.WeightingSchemeName(ic_weights="Nonexistent Scheme")
    with pytest.raises(exceptions.NameNotFoundError):
        crud.get_scheme_id_by_weight_string(test_db, invalid_weights)


def test_get_item_id_by_name(
        test_db
        ):
    # Testing successful retrieval
    item_id = crud.get_item_id_by_name(
        test_db,
        "Item 76101"
        )
    assert isinstance(
        item_id,
        schemas.ItemID
        ), "Should return a Pydantic instance of ItemID"
    assert item_id.item_id == "76101", "Should fetch correct ID for valid item name"

    # Testing retrieval failure
    with pytest.raises(
            exceptions.NameNotFoundError
            ):
        crud.get_item_id_by_name(
            test_db,
            "Nonexistent Item"
            )


def test_get_ic_weights_by_scheme_id_success(test_db):
    scheme = schemas.WeightingSchemeID(scheme_id=1)  # Assuming this scheme has weights set up correctly
    weights_dict = crud.get_ic_weights_by_scheme_id(test_db, scheme)
    assert isinstance(weights_dict, schemas.WeightsDict), "Should return a WeightsDict instance"
    total_weight = sum(weight.weight for weight in weights_dict.weights.values())
    assert 0.9999 <= total_weight <= 1.0001, "Weights should sum to approximately 1"


def test_get_ic_weights_by_scheme_id_failure_no_weights(test_db):
    scheme = schemas.WeightingSchemeID(scheme_id=999)  # Assuming no such scheme exists
    with pytest.raises(exceptions.NameNotFoundError) as exc_info:
        crud.get_ic_weights_by_scheme_id(test_db, scheme)
    assert "Weights not found for scheme ID = 999" in str(
        exc_info.value
        ), "The error message should indicate the weights were not found"



@pytest.mark.usefixtures("valid_data")
def test_fetch_results(test_db, valid_data):
    """
    Test to fetch and validate LCI results based on the data provided by the valid_data fixture.
    """
    # Retrieve test parameters dynamically
    item_id = schemas.ItemID(item_id=valid_data["item_ids"][0])
    geo_id = schemas.GeoID(valid_data["geo_ids"][0])
    scheme_id = schemas.WeightingSchemeID(scheme_id=valid_data["scheme_ids"][0])
    stage = valid_data["stages"][0]
    impact_category = valid_data["impact_categories"][0]

    # Call the function under test
    lci_result = crud.fetch_results(
        session=test_db,
        item_id=item_id,
        geo_id=geo_id,
        scheme_id=scheme_id,
        stages=[schemas.LCStageID(lc_stage_id=stage)],
        impact_categories=[schemas.ImpactCategoryID(ic_id=impact_category)]
        )

    # Dynamically fetch expected values
    expected_single_score = valid_data["single_scores"][(item_id.item_id, geo_id.geo_id, scheme_id.scheme_id)]
    expected_stage_value = valid_data["weighted_results"][
        (item_id.item_id, geo_id.geo_id, impact_category, stage, scheme_id.scheme_id)]
    expected_impact_category_value = expected_stage_value  # Assuming it should match

    # Assertions to ensure the returned data is correct
    assert lci_result.single_score.lcia_value == expected_single_score, "Single score does not match expected value"
    assert len(lci_result.stage_values) == 1, "Incorrect number of stage values returned"
    assert len(lci_result.impact_category_values) == 1, "Incorrect number of impact category values returned"

    assert lci_result.stage_values[schemas.LCStageID(
        lc_stage_id=stage
        )].lcia_value == expected_stage_value, "Stage value does not match expected"
    assert lci_result.impact_category_values[schemas.ImpactCategoryID(
        ic_id=impact_category
        )].lcia_value == expected_impact_category_value, "Impact category value does not match expected"


def test_check_results_exist(test_db):
    # Case where results should exist
    valid_item_id = schemas.ItemID(item_id="76101")
    valid_geo_id = schemas.GeoID(1)
    valid_scheme_id = schemas.WeightingSchemeID(scheme_id=1)

    assert crud.check_results_exist(
        session=test_db,
        item_id=valid_item_id,
        geo_id=valid_geo_id,
        scheme_id=valid_scheme_id
        ), "Should find results for valid IDs"

    # Case where no results should exist
    invalid_item_id = schemas.ItemID(item_id="99999")  # Assuming this item ID does not exist
    assert not crud.check_results_exist(
        session=test_db,
        item_id=invalid_item_id,
        geo_id=valid_geo_id,
        scheme_id=valid_scheme_id
        ), "Should not find results for invalid item ID"



@pytest.mark.usefixtures("valid_data")
def test_get_all_min_max_values(test_db, valid_data):
    """
    Test to fetch and validate min and max values for single scores and impact categories.
    """
    # Retrieve the scheme ID and impact category IDs for the test
    scheme_id = schemas.WeightingSchemeID(scheme_id=valid_data["scheme_ids"][0])
    impact_category_ids = [schemas.ImpactCategoryID(ic_id=ic_id) for ic_id in valid_data["impact_categories"]]

    # Call the function under test
    min_max_values = crud.get_min_max_values(
        session=test_db,
        scheme_id=scheme_id,
        impact_category_ids=impact_category_ids
    )

    # Filter the expected single scores for the specific scheme_id
    expected_single_scores_for_scheme = {
        key: value for key, value in valid_data["single_scores"].items() if key[2] == scheme_id.scheme_id
    }

    # Validate single score min and max values
    expected_single_score_max = max(expected_single_scores_for_scheme.values())
    expected_single_score_min = min(expected_single_scores_for_scheme.values())

    assert min_max_values.single_score_max.lcia_value == expected_single_score_max, \
        "Single score max value does not match expected value"
    assert min_max_values.single_score_min.lcia_value == expected_single_score_min, \
        "Single score min value does not match expected value"

    # Further assertions can be added to validate impact category min and max values if necessary




if __name__ == "__main__":
    import sys

    pytest.main(
        ["-s", sys.argv[0]]
        )
