# /YourProject/tests/utils/api_helpers.py
from API.schemas import ItemID, LCStageID
from sqlmodel import Session
from tests.utils.db_helpers import get_valid_code_agb, get_valid_stages

def create_valid_payload(code_agb: ItemID, stages: list[LCStageID]):
    """
    Create a valid payload based on the provided code_agb and stages.

    Args:
        code_agb (ItemID): The valid code_agb.
        stages (list[LCStageID]): The list of valid stage IDs.

    Returns:
        dict: The valid payload.
    """
    return {
        "items": [code_agb.dict()],
        "amounts": {"root": [1.0]},  # Assuming weights need to sum to 1
        "weighting_scheme_name": {"root": [1.0]},
        "stages": [stage.dict() for stage in stages]
    }

def create_invalid_payload(session: Session, invalid_code_agb=False, invalid_amounts=False, invalid_ic_weights=False, invalid_stages=False):
    """
    Create an intentionally invalid payload for negative testing.

    Args:
        session (Session): The test database session to fetch valid data.
        invalid_code_agb (bool): If True, generate an invalid code_agb.
        invalid_amounts (bool): If True, generate invalid amounts.
        invalid_ic_weights (bool): If True, generate invalid impact category weights.
        invalid_stages (bool): If True, generate invalid stages.

    Returns:
        dict: The invalid payload.
    """
    valid_code_agb = get_valid_code_agb(session)
    valid_stages = get_valid_stages(session)

    payload = {
        "items": [ItemID(value=99999).dict()] if invalid_code_agb else [ItemID(value=valid_code_agb[0].lcia_value).dict()],
        "amounts": {"root": [0.5] if invalid_amounts else [1.0]},
        "weighting_scheme_name": {"root": [0.5] if invalid_ic_weights else [1.0]},
        "stages": ["unknown_stage"] if invalid_stages else [LCStageID(value=valid_stages[0].lcia_value).dict()]
    }
    return payload
