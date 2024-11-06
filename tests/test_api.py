import pytest


@pytest.mark.usefixtures("valid_data")
def test_fetch_lci_items_endpoint(test_client, valid_data):
    """
    Test the fetch_lci_items endpoint with valid input data.
    """
    # Extract item_ids and geo_ids from the valid_data fixture
    item_ids = [valid_data["item_ids"][0], valid_data["item_ids"][1]]
    geo_ids = [valid_data["geo_ids"][0], valid_data["geo_ids"][1]]

    # Prepare the input data using UniqueID for unique keys
    input_data = {
        "items": {
            f"{item_ids[0]}-{geo_ids[0]}": 0.5,
            f"{item_ids[1]}-{geo_ids[1]}": 0.5,
        },
        "weighting_scheme_name": "ef31_r0510"
    }
    openapi_schema = get_openapi(title="Test API", version="1.0.0", routes=app.routes)
    print("OpenAPI Schema:", openapi_schema)
    # Make the POST request to the endpoint
    response = test_client.post("/fetch-lci-items/", json=input_data)
    print(response.json())
    # Check for a successful response (status code 200)
    assert response.status_code == 200

    # Check if the response contains the expected keys
    response_data = response.json()
    assert "single_score" in response_data
    assert "stage_values" in response_data
    assert "impact_category_values" in response_data


if __name__ == "__main__":
    import sys

    pytest.main(['-s', sys.argv[0]])
