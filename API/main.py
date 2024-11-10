"""
This module defines the FastAPI application and its endpoints.
It initializes the database and provides endpoints for fetching LCI values.
"""
import asyncio
import logging
import traceback

from fastapi import (
    FastAPI,
    Depends,
    Request,
    HTTPException,
)
from fastapi.openapi.utils import get_openapi
from sqlmodel import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from API import (crud, processors, database, schemas, dependencies, exceptions, logging_setup, exception_handlers,
                 config)

app = FastAPI()
global_config = None


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Custom API",
        version="1.0.0",
        description="This is a custom OpenAPI schema.",
        routes=app.routes,
    )

    # Filter out schemas where 'include_in_docs' is False in the model config
    filtered_schemas = {}
    for key, value in openapi_schema["components"]["schemas"].items():
        try:
            # Retrieve the schema class from the `schemas` module
            schema_class = getattr(schemas, key, None)

            # Exclude schema if 'include_in_docs' is set to False
            if not (schema_class and hasattr(schema_class, 'model_config') and
                    schema_class.model_config.get('json_schema_extra', {}).get('include_in_docs', True) is False):
                filtered_schemas[key] = value
        except AttributeError:
            # If the schema doesn't have model_config or include_in_docs, include it
            filtered_schemas[key] = value

    openapi_schema["components"]["schemas"] = filtered_schemas

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set the custom OpenAPI function
app.openapi = custom_openapi
logging_setup.setup_logging()
logger = logging.getLogger('uvivorn')


@app.on_event("startup")
async def on_startup() -> None:
    """
    Event handler for the FastAPI startup event.

    This function performs the following actions:
    1. Initializes the database by creating necessary tables.
    2. Checks if log levels need adjustment and schedules the adjustment if necessary.
    """
    try:
        logger.info("Setting up and validating the database. This might take a minute.")
        database.create_tables()
        logger.info("Database setup completed successfully.")
    except Exception as database_error:
        logger.error(f"An error occurred during database setup: {database_error}")
        raise
    # adjust the log level for the sql logger after db creation
    logging_setup.adjust_sql_log_level()

    # Check if log level adjustment is needed
    app_file_handler = logging_setup.needs_log_level_adjustment()

    if app_file_handler:
        logger.debug("Current log levels differ from desired levels. Scheduling log level adjustment.")
        asyncio.create_task(logging_setup.adjust_log_level(app_file_handler))


@app.get("/test-exception")
async def test_exception():
    """
    Endpoint to test exception handling and logging.
    Raises an HTTPException with a 400 Bad Request status.
    """
    # Log an info message to check if it's captured or suppressed
    logger.info("This is an info message before raising an exception.")

    # Raise an exception to trigger the error handler
    raise HTTPException(status_code=400, detail="This is a test exception to check logging")


# HTTP exception handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return exception_handlers.handle_exception(request, exc)


# General exception handler for other uncaught exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return exception_handlers.handle_exception(request, exc)


@app.get("/settings")
async def get_app_settings(settings: config.DebugSettings = Depends(dependencies.get_debug_settings)):
    """
    Return the current application settings. This will be probably removed in shipping.
    """
    return settings.dict()


@app.get("/items/", response_model=schemas.AllItems)
def read_items_info(session: Session = Depends(dependencies._get_db_session)):
    """
    Retrieves all items and returns them in a structured JSON format.

    Each item is represented by a unique key in the format 'itemid-country_acronym',
    where 'itemid' refers to the item's unique identifier, and 'country_acronym' is the
    ISO 3166-1 alpha-3 code for the country associated with the item.

    The values associated with each key contain detailed information about the product, including:
    - `product_name`: The name of the product (e.g., 'Lamb, neck, braised or boiled').
    - `country`: The full name of the country (e.g., 'France').
    - `international_code`: The numeric international code for the country (e.g., 250 for France).
    - `group`: The main category the product belongs to (e.g., 'viandes, œufs, poissons').
    - `subgroup`: The subcategory of the product (e.g., 'viandes cuites').
    - `proxy`: A boolean indicating whether the data for this item is a proxy (i.e., estimated or inferred data).

    The response is structured as a dictionary where the keys are strings in the format 'itemid-country_acronym',
    and the values are `ItemInfo` objects containing the product details.

    ### Example Response:
    ```json
    {
      "21508-FRA": {
        "product_name": "Lamb, neck, braised or boiled",
        "country": "France",
        "international_code": 250,
        "group": "viandes, œufs, poissons",
        "subgroup": "viandes cuites",
        "proxy": false
      },
      "21519-FRA": {
        "product_name": "Lamb, leg, braised",
        "country": "France",
        "international_code": 250,
        "group": "viandes, œufs, poissons",
        "subgroup": "viandes cuites",
        "proxy": false
      }
    }
    ```

    Returns:
        A JSON object containing a dictionary where each key represents a unique product identifier and each value
        contains detailed information about the corresponding product.
    """
    return crud.get_all_items_info(session)


@app.post("/calculate-recipe/", response_model=schemas.OutputData)
async def calculate_recipe(
        data: schemas.InputData,
        session: Session = Depends(dependencies._get_db_session),
):
    """
    Calculates the environmental impact of a recipe based on provided items, their mass and a weighting scheme. The
    endpoint processes the input data, retrieves Life Cycle Impact Assessment (LCIA) data for each item in the recipe
    from the Agribalyse database, and calculates a single score for each item and the entire recipe based on the given
    weighting scheme. These results are organized by life cycle stages and impact categories, with a single score and
    grade assigned to both each item and the recipe.

    ### Input Data:
    The input data includes the items that make up the recipe and - optionally - a specific weighting scheme used to
    assess the environmental impact. If no weighting scheme is specified, the default delphi_r0110 is being used. Each
    item is associated with a unique identifier and a specified amount in kilograms. The weighting scheme ensures that
    the impact is calculated consistently according to a predefined method.

    ### Input Data:

    The input data consists of a nested dictionary with two main parts: `items` and either `weighting_scheme_name`
    or `weighting_scheme_id`.

    - **Items**: Represented as a dictionary where each key is a unique identifier in the format
      `item_id-country_acronym`, and the value is the amount (weight) of the item in kilograms.
      - `item_id`: The unique identifier of the item.
      - `country_acronym`: The ISO 3166-1 alpha-3 code representing the country of origin.
      - `Amount`: A float value representing the weight of the item in kilograms.

    - **[OPTIONAL] Weighting Scheme**: Provided as either:
      - **weighting_scheme_name**: A string representing the name of the weighting scheme.
      - **weighting_scheme_id**: An integer representing the numerical ID of the weighting scheme.

    ### Process:
    The environmental impact of the recipe is calculated using data from the Agribalyse database. For each item in the
    recipe, the system retrieves life cycle impact assessment (LCIA) values and processes them through several steps to
    derive environmental impact scores. These scores include aggregated values for both life cycle stages and impact
    categories, as well as single scores for individual items and the entire recipe. The system assigns grades for the
    life cycle stages, impact categories, and single scores for both the items and the recipe.

    This process ensures that environmental impacts are assessed consistently across different items, stages, and
    categories.
    The steps involve normalizing the data and aggregating values based on the specified weighting scheme. The results
    are then scaled and graded, and adjustments are made when proxy data (estimated or inferred data) is involved.

    This process consists of the following key categories:

    1. **Selection**:
       - The relevant **impact categories** are selected based on the non-zero impact category weights from the default
       or selected weighting scheme.
       - The **life cycle stages** considered for each impact category include:
         - Agricultural stage (abbreviation: "agri")
         - Processing (abbreviation: "proc")
         - Transports (abbreviation: "transp")
         - Retail (abbreviation: "retail")
       - All of these stages are considered for each impact category, except for the **biodiversity impact category**,
         which is assumed to occur only in the agricultural stage.

    2. **Normalization**:
       - The selected values from the Agribalyse database are normalized by a specific reference value for each impact
       category. These values are derived in accordance with Environmental Footprint 3.1 reference literature. For
       biodiversity, a value published in the context of Agribalyse is being used.

    3. **Weighting**:
       - After normalization, the normalized impact values are weighted based on the applicable weighting scheme.


    4. **Aggregation**:
       - **Life Cycle Stages (LC Stages)**: For each selected  life cycle stage (e.g., Agriculture, Processing),
       the normalized weighted values for all selected impact categories within that stage are **summed**.
       This aggregation produces a single value for each selected stage, combining all relevant impact category
       contributions.
       - **Impact Categories (IC)**: For each selected impact category (e.g., Climate Change, Ozone Depletion), the
       weighted normalized values across all selected life cycle stages are **summed** to produce an aggregated score.
       This score represents the total environmental impact in that specific category for the entire recipe or item.

    5. **Single Score Calculation**:
       - The **single score** represents the overall environmental impact of the recipe or item.
       - It is calculated as a **sum** of the aggregated, weighted and normalized values of all selected impact
       categories.
       - This single score is **not normalized** and reflects the total environmental burden of the recipe.

    6. **Grading and Scaled Values**:
       - **Scaled values** are computed for each life cycle stage and impact category, as well as the single score, by
         applying **log min-max scaling** on the weighted normalized values within their corresponding domains
         (impact category, life cycle stage, or single score).
       - Scaling ensures that all values fall between 0 and 1, enabling comparison between different stages or impact
         categories.
       - Only non-proxy data is used in calculating the min and max values for scaling.
       - For proxy data, the values are **truncated**:
         - Any value greater than the max value from non-proxy data is set to the max value.
         - Any value lower than the min value from non-proxy data is set to the min value.
       - Based on the scaled value, a **grade** (e.g., A, B, C) is assigned to indicate the performance in that stage
         or category.
       - **Aggregation of Scaled Values**: When aggregating scaled values (e.g., to get an overall grade for the
         aggregated values of an impact category across multiple life cycle stages), we use a **renormalized Euclidean
         distance formula**:
         - Aggregated Scaled Value = sqrt((scaled_value_1^2 + scaled_value_2^2 + ... + scaled_value_n^2) / n)
         - Here, `n` is the number of nonzero impact categories or stages being aggregated.

    7. **Recipe Calculation**:
       - The calculation for the recipe follows a similar process as for individual items:
         1. **Normalized Weighted Values**: For each impact category, the normalized weighted values are first
            aggregated for each item in the recipe.
         2. **Item Amount**: Each item's aggregated, weighted and normalized  impact category value is then
         **weighted by the item amount** (in kilograms) present in the recipe.
         3. **Summation**: The aggregated, weighted and normalized values across all items are **summed up** to get
         the total contribution of each impact category for the entire recipe.
         4. **Single Score Calculation**: The **single score** for the recipe is calculated as a **sum** of the
         aggregated, weighted and normalized values of all selected impact categories, following the same method as the
         item-level calculation. This score represents the overall environmental impact of the entire recipe and
         is **not scaled**.

    8. **Proxy Flag**:
       - The system determines whether any **proxy data** (i.e., estimated or inferred data) is used at the recipe or
         item level.
       - If proxy data is used, the values are adjusted accordingly during scaling, and the system flags the proxy
         usage.


    ### Response Structure:
    The response includes detailed information on:
    - **General Information**:
      - The weighting scheme used.
      - Whether proxy data is present in any item or stage.
      - The total mass of the recipe in kilograms.
    - **Recipe Info**:
      - Overall single score for the entire recipe.
      - Aggregated scores for life cycle stages (e.g., Agriculture, Transformation).
      - Aggregated scores for environmental impact categories (e.g., Climate Change, Ozone Depletion).
    - **Item Results**:
      - Individual environmental impact scores for each item in the recipe.
      - Breakdown of each item's score by life cycle stages (e.g., Agriculture, Transformation).
      - Breakdown of each item's score by impact categories (e.g., Climate Change, Ozone Depletion).
      - For each item, whether proxy data is used (indicating if any estimated data was involved).

    ### Returns:
    The response is structured as a dictionary with two main keys: `recipe_info` and `item_results`.

    - **recipe_info** (dict):
      - **"General Info"** (dict):
        - `"Weighting Scheme"` (str): The name or ID of the weighting scheme used.
        - `"contains_proxy"` (bool): Indicates whether proxy data is present in any item or stage.
        - `"Overall Mass"` (str): The total mass of the recipe in kilograms (e.g., `"1.7 kg"`).

      - **"Single Score"** (dict):
        - `"Single Score"` (float): The overall environmental impact score for the entire recipe.
        - `"Grade"` (str): A letter representing the performance grade (e.g., `"A"`).
        - `"Scaled Value"` (float): The normalized score, scaled between 0 and 1.

      - **"Items"** (dict):
        - Keys (str): Item identifiers in the format `"item_id-country_acronym"`.
        - Values (str): The amounts of each item in kilograms (e.g., `"1.2 kg"`).

      - **"Stages"** and **"Impact Categories"** (dict):
        - Keys (str): Names of the life cycle stages (e.g., `"Agriculture"`) or impact categories
        (e.g., `"Climate Change"`).
        - Values (dict):
          - `"lcia_value"` (float): The aggregated value for the stage or impact category.
          - `"Grade"` (str): A letter representing the performance grade (e.g., `"B"`).
          - `"Scaled Value"` (float): The normalized score, scaled between 0 and 1.

    - **item_results** (dict):
      - Keys (str): Item identifiers in the format `"item_id-country_acronym"`.
      - Values (dict): Contains detailed environmental impact results for each item:
        - **"Single Score"** (dict): The impact score for the item.
        - **"Stages"** and **"Impact Categories"** (dict): Same structure as `recipe_info`, but specific to each item.
        - `"contains_proxy"` (bool): Indicates whether proxy data is used for the item.

    ### Example Request:
    ```json
    {
     "items": {
       "20134-FRA": 1.2,
       "24070-FRA": 0.5
     },
     "weighting_scheme_name": "ef31_r0510"
    }
    ```

    ### Example Response:
    ```json
    {
     "Recipe Info": {
       "General Info": {
         "Weighting Scheme": "ef31_r0510",
         "contains_proxy": false,
         "Overall Mass": "1.7 kg"
       },
       "Single Score": {
         "Single Score": "float_value",
         "Grade": "A",
         "Scaled Value": "float_value"
       },
       "Items": {
         "20134-FRA": "1.2 kg",
         "more_items": "..."
       },
       "Stages": {
         "Agriculture": {
           "lcia_value": "float_value",
           "Grade": "B",
           "Scaled Value": "float_value"
         },
         "more_stages": "..."
       },
       "Impact Categories": {
         "Climate change": {
           "lcia_value": "float_value",
           "Grade": "A",
           "Scaled Value": "float_value"
         },
         "more_impact_categories": "..."
       }
     },
     "Item Results": {
       "20134-FRA": {
         "Single Score": {
           "Single Score": "float_value",
           "Grade": "A",
           "Scaled Value": "float_value",
           "contains_proxy": false
         },
         "Stages": {
           "Agriculture": {
             "lcia_value": "float_value",
             "Grade": "B",
             "Scaled Value": "float_value"
           },
           "more_stages": "..."
         },
         "Impact Categories": {
           "Climate change": {
             "lcia_value": "float_value",
             "Grade": "A",
             "Scaled Value": "float_value"
           },
           "more_impact_categories": "..."
         }
       },
       "more_items": "..."
     }
    }
    ```
    """
    try:
        # Process input data to convert country acronyms to geo_ids
        processors.process_input_data(data, session)

        # Fetch the corresponding weighting scheme name or ID if necessary
        if not data.weighting_scheme_name and data.weighting_scheme_id:
            data.weighting_scheme_name = crud.get_name_by_id(session, data.weighting_scheme_id)

        if not data.weighting_scheme_id and data.weighting_scheme_name:
            data.weighting_scheme_id = crud.get_scheme_id_by_weight_string(session, data.weighting_scheme_name)

        # Get the impact category weights and life cycle stages
        impact_category_weights = crud.get_ic_weights_by_scheme_id(session, data.weighting_scheme_id)
        impact_categories = list(impact_category_weights.weights.keys())
        lc_stages = [
            schemas.LCStageID(1),
            schemas.LCStageID(2),
            schemas.LCStageID(4),
            schemas.LCStageID(5)
        ]

        # Prepare to store results for all items
        item_results = []
        proxy_flags = {}
        for unique_id, item_amount in data.items.items():
            item_id = unique_id.item_id
            geo_id = unique_id.geo_id

            # Fetch the proxy flag
            proxy_flag = crud.get_proxy_flag(session, item_id, geo_id)
            proxy_flags[unique_id] = proxy_flag

            # Fetch the results for the item, geo, and scheme
            lcia_result = processors.get_results(
                session, item_id, geo_id, data.weighting_scheme_id, impact_categories, lc_stages
            )

            # Append the result to the item_results list
            item_results.append(lcia_result)

        # Fetch the min and max values for grading
        min_max_values = crud.get_min_max_values(session, data.weighting_scheme_id, impact_categories, lc_stages)

        # Apply grading scheme to the item results
        graded_item_results = [processors.apply_grading_scheme(item_result, min_max_values) for item_result in
                               item_results]

        # Calculate recipe scores based on the graded item results
        recipe_scores = processors.calculate_recipe(graded_item_results)

        # Collect all unique stage IDs and impact category IDs from recipe and item results
        stage_ids = set()
        impact_category_ids = set()

        # Collect from recipe scores
        stage_ids.update(recipe_scores.stage_values.keys())
        impact_category_ids.update(recipe_scores.impact_category_values.keys())

        # Collect from graded LCIA results for all items
        for item_result in graded_item_results:
            stage_ids.update(item_result.stage_values.keys())
            impact_category_ids.update(item_result.impact_category_values.keys())

        # Perform a single lookup for all stage and impact category names
        stage_names = {stage_id: crud.get_name_by_id(session, stage_id) for stage_id in stage_ids}
        impact_category_names = {ic_id: crud.get_name_by_id(session, ic_id) for ic_id in impact_category_ids}

        # Prepare the output data with all necessary information passed to the schema
        output_data = schemas.OutputData(
            input_data=data,
            graded_lcia_results=graded_item_results,
            recipe_scores=recipe_scores,
            proxy_flags=proxy_flags,
            stage_names=stage_names,
            impact_category_names=impact_category_names
        )

        return output_data

    except exceptions.InvalidItemCountryAcronymFormatError as custom_error:
        raise HTTPException(status_code=400, detail=f"Invalid country acronym: {custom_error}")

    except (exceptions.MissingWeightingSchemeError, exceptions.WeightingSchemeNameNotFoundError,
            exceptions.WeightingSchemeIDNotFoundError) as custom_error:
        raise HTTPException(status_code=400, detail=str(custom_error))

    except Exception as exc:
        tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        raise HTTPException(status_code=500, detail=tb_str)


if __name__ == "__main__":
    print("This is only a library. Nothing will happen when you execute it")
