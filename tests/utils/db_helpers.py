# /YourProject/tests/utils/db_helpers.py
from sqlmodel import Session, select
from API.models import Meta, Stage, WeightingRobustness
from API.schemas import ItemID, LCStageID, ICWeight

def get_valid_code_agb(session: Session):
    """
    Fetch valid code_agb from the Meta table.

    Args:
        session (Session): The database session.

    Returns:
        List[ItemID]: A list of valid code_agb values as ItemID.
    """
    statement = select(Meta.item_id)
    results = session.execute(statement).scalars().all()
    return [ItemID(value=result) for result in results]

def get_valid_stages(session: Session):
    """
    Fetch valid stage IDs from the Stage table.

    Args:
        session (Session): The database session.

    Returns:
        List[LCStageID]: A list of valid stage IDs as LCStageID.
    """
    statement = select(Stage.lc_stage_id)
    results = session.execute(statement).scalars().all()
    return [LCStageID(value=result) for result in results]

def get_valid_weights(session: Session):
    """
    Fetch valid weights from the WeightingRobustness table.

    Args:
        session (Session): The database session.

    Returns:
        List[ICWeight]: A list of valid weights as ICWeight.
    """
    statement = select(WeightingRobustness.weighting_delphi)
    results = session.execute(statement).scalars().all()
    return [ICWeight(value=result) for result in results]
