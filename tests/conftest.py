import pytest
from fastapi.testclient import TestClient
from sqlmodel import (
    create_engine,
    Session,
    SQLModel,
)

import API.models as models
from API import dependencies, database
from API.main import app


def create_geographies(geo_ids):
    """
    Create geography data for a list of geo IDs.

    Args:
        geo_ids (list): A list of geographic IDs.

    Returns:
        dict: A dictionary of geography data with geo_id as keys.
    """
    geographies = {
        geo_id: {
            "geo_id": geo_id,
            "international_code": 100 + geo_id,
            "geo_shorthand_2": f"C{geo_id}",
            "geo_shorthand_3": f"CO{geo_id}",
            "country_name": f"country {geo_id}"
        }
        for geo_id in geo_ids
    }
    return geographies


def populate_geographies(session, geographies):
    """
    Populate the database with geography data.

    Args:
        session (Session): The database session.
        geographies (dict): A dictionary of geography data with geo_id as keys.
    """
    geo_models = [models.Geographies(**geo_info) for geo_info in geographies.values()]
    session.add_all(geo_models)
    session.commit()


def populate_groups(
        session, group_ids
):
    groups = []
    for group_id in group_ids:
        groups.append(
            models.Groups(
                group_id=group_id, group_name=f"Group {group_id}"
            )
        )
    session.add_all(
        groups
    )


def populate_subgroups(
        session, subgroup_ids
):
    subgroups = []
    for subgroup_id in subgroup_ids:
        subgroups.append(
            models.Subgroups(
                subgroup_id=subgroup_id, subgroup_name=f"Subgroup {subgroup_id}"
            )
        )
    session.add_all(
        subgroups
    )


def populate_metadata(
        session, item_ids, geo_ids
):
    metadata = []
    for item_id, geo_id in zip(
            item_ids, geo_ids
    ):
        metadata.append(
            models.MetaData(
                item_id=item_id, geo_id=geo_id, name_lci=f"Item {item_id}",proxy_flag=False
            )
        )
    session.add_all(
        metadata
    )


def populate_life_cycle_stages(
        session, stage_ids
):
    stages = [models.LifeCycleStages(
        lc_stage_id=stage_id, lc_stage_shorthand=f"Stage{stage_id}", lc_name=f"Phase {stage_id}"
    ) for stage_id in stage_ids]
    session.add_all(
        stages
    )


def populate_impact_categories(session, category_ids):
    impact_categories = [
        models.ImpactCategories(
            ic_id=ic_id,
            ic_name=f"Category {ic_id}",
            ic_shorthand=f"C{ic_id}",
            normalization_value=1.0,  # Set default or appropriate value
            normalization_unit="kg CO2e"  # Set default or appropriate unit
        )
        for ic_id in category_ids
    ]
    session.add_all(impact_categories)
    session.commit()


def populate_weighting_schemes(
        session, weighting_names
):
    schemes = [models.WeightingSchemes(
        scheme_id=id, name=weighting_name
    ) for id, weighting_name in enumerate(
        weighting_names, start=1
    )]
    session.add_all(
        schemes
    )


def create_single_scores(item_ids, geo_ids, scheme_ids):
    single_scores = {
        (item_id, geo_id, scheme_id): 50.0 + scheme_id + (i % 10)
        for i, (item_id, geo_id) in enumerate(zip(item_ids, geo_ids))
        for scheme_id in scheme_ids
    }
    return single_scores


def populate_single_scores(
        session, single_scores
):
    single_scores = [models.SingleScores(
        item_id=key[0], geo_id=key[1], scheme_id=key[2], single_score=value
    ) for key, value in single_scores.items()]
    session.add_all(
        single_scores
    )


def create_impact_category_weights(scheme_ids, impact_categories):
    ic_weights = {}
    for scheme_id in scheme_ids:
        num_categories = len(impact_categories)
        # Assign each category an initial weight
        weights = [round(1.0 / num_categories, 2) for _ in range(num_categories)]
        # Adjust the last weight to make sure the sum is exactly 1.0
        weights[-1] = round(1.0 - sum(weights[:-1]), 2)

        # Store weights in the dictionary
        for ic_id, weight in zip(impact_categories, weights):
            ic_weights[(scheme_id, ic_id)] = weight

    return ic_weights


def populate_impact_category_weights(
        session, ic_weights
):
    weights = [models.ImpactCategoryWeights(
        scheme_id=key[0], ic_id=key[1], ic_weight=value
    ) for key, value in ic_weights.items()]
    session.add_all(
        weights
    )


def create_weighted_results(
        item_ids, geo_ids, scheme_ids, impact_categories, stages
):
    weighted_results = {}
    for item_id, geo_id in zip(
            item_ids, geo_ids
    ):
        for scheme_id in scheme_ids:
            for ic_id in impact_categories:
                for stage_id in stages:
                    # Simplified calculation example
                    weighted_value = 10 * ic_id * stage_id * (scheme_id % 2 + 1)  # Example formula
                    weighted_results[(item_id, geo_id, ic_id, stage_id, scheme_id)] = weighted_value
    return weighted_results


def populate_weighted_results(
        session, weighted_results
):
    results = [models.WeightedResults(
        item_id=key[0], geo_id=key[1], ic_id=key[2], lc_stage_id=key[3], scheme_id=key[4], weighted_value=value
    ) for key, value in weighted_results.items()]
    session.add_all(
        results
    )


def create_normalized_lcia_values(item_ids, geo_ids, stages, impact_categories):
    normalized_lcia_values = {}
    for item_id in item_ids:
        for geo_id in geo_ids:
            for stage_id in stages:
                for ic_id in impact_categories:
                    # Predictable values for testing
                    normalized_value = 10 + ic_id * 0.1 + stage_id
                    non_normalized_value = normalized_value * 2
                    key = (item_id, geo_id, stage_id, ic_id)
                    normalized_lcia_values[key] = {
                        'normalized_lcia_value': normalized_value,
                        'non_normalized_lcia_value': non_normalized_value
                    }
    return normalized_lcia_values


def populate_normalized_lcia_values(session, normalized_lcia_values):
    entries = []
    for (item_id, geo_id, stage_id, ic_id), values in normalized_lcia_values.items():
        entry = models.NormalizedLCIAValues(
            item_id=item_id,
            geo_id=geo_id,
            ic_id=ic_id,
            lc_stage_id=stage_id,
            normalized_lcia_value=values['normalized_lcia_value'],
            non_normalized_lcia_value=values['non_normalized_lcia_value']
        )
        entries.append(entry)
    session.add_all(entries)


def setup_test_data():
    # Basic data definitions
    item_ids = ["76101", "76102", "96778", "1029_1"]
    geo_ids = [1, 2, 3, 4]
    geographies = create_geographies(geo_ids)
    group_ids = [1, 2]
    subgroup_ids = [1, 2]
    impact_categories = list(range(1, 18))
    stages = list(range(1, 5))
    weighting_names = ["weighting_delphi", "ef31_r0510", "Scheme C"]
    scheme_ids = range(1, len(weighting_names) + 1)

    # Creating single scores dynamically
    single_scores = create_single_scores(
        item_ids, geo_ids, scheme_ids
    )

    # Creating weighted results dynamically
    weighted_results = create_weighted_results(
        item_ids, geo_ids, scheme_ids, impact_categories, stages
    )

    # Creating impact category weights dynamically
    ic_weights = create_impact_category_weights(
        scheme_ids, impact_categories
    )

    normalized_lcias = create_normalized_lcia_values(item_ids, geo_ids, stages, impact_categories)

    data = {
        "item_ids": item_ids,
        "geo_ids": geo_ids,
        "geographies": geographies,
        "scheme_ids": scheme_ids,
        "impact_categories": impact_categories,
        "stages": stages,
        "weighting_names": weighting_names,
        "group_ids": group_ids,
        "subgroup_ids": subgroup_ids,
        "single_scores": single_scores,
        "weighted_results": weighted_results,
        "weighting_scheme_name": ic_weights,
        "normalized_lcias": normalized_lcias
    }
    return data


@pytest.fixture(
    scope="module"
)
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Populate the database with the necessary data
        data = setup_test_data()
        populate_geographies(session, data["geographies"])
        populate_groups(session, data["group_ids"])
        populate_subgroups(session, data["subgroup_ids"])
        populate_life_cycle_stages(session, data["stages"])
        populate_impact_categories(session, data["impact_categories"])
        populate_metadata(session, data["item_ids"], data["geo_ids"])
        populate_weighting_schemes(session, data["weighting_names"])
        populate_single_scores(session, data["single_scores"])
        populate_weighted_results(session, data["weighted_results"])
        populate_impact_category_weights(session, data["weighting_scheme_name"])
        populate_normalized_lcia_values(session, data["normalized_lcias"])

        session.commit()
        yield session


@pytest.fixture(
    scope="module"
)
def valid_data():
    return setup_test_data()


@pytest.fixture(scope="module")
def test_client(test_db):
    # Create a new override for `database.get_session` that yields the `test_db` session
    def override_get_session():
        yield test_db

    # Apply the override to the FastAPI app for `database.get_session` first
    app.dependency_overrides[database.get_session] = override_get_session

    # Now apply the `dependencies._get_db_session` that depends on `database.get_session`
    def override_get_db_session(session: Session = test_db):
        return session

    # Override the FastAPI app dependency
    app.dependency_overrides[dependencies._get_db_session] = override_get_db_session

    # Create and yield the TestClient
    with TestClient(app) as client:
        yield client

    # Clean up overrides after test
    app.dependency_overrides.clear()


if __name__ == "__main__":
    print(
        "This is a utility module for setting up and testing the database with pytest."
    )
    print(
        "To run tests, use pytest command-line tools."
    )
