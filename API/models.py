import inspect
import sys

from sqlmodel import SQLModel, Field, Relationship, Boolean, Column
from typing import List, Optional


class ModelRegistry:
    _registry = {}

    def __init__(self):
        self.register_all()

    def register_all(self):
        # Inspect current module to find all SQLModel subclasses
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if inspect.isclass(obj) and issubclass(obj, SQLModel) and obj is not SQLModel:
                self._registry[obj.__tablename__.lower()] = obj

    @classmethod
    def get_model(cls, name):
        """Retrieve a model class by its table name."""
        model = cls._registry.get(name.lower(), None)
        if model is None:
            print(f"Model not found: {name}")
        return model


class ImpactCategories(SQLModel, table=True):
    ic_id: int = Field(primary_key=True)
    ic_name: str
    ic_shorthand: str
    normalization_value: float = Field(...)
    normalization_unit: str = Field(...)
    normalized_lcis: List['NormalizedLCIAValues'] = Relationship(back_populates="impact_categories")
    impact_category_weights: List['ImpactCategoryWeights'] = Relationship(back_populates="impact_categories")
    weighted_results: List['WeightedResults'] = Relationship(back_populates="impact_categories")


class LifeCycleStages(SQLModel, table=True):
    lc_stage_id: int = Field(primary_key=True)
    lc_stage_shorthand: str
    lc_name: str
    normalized_lcis: List['NormalizedLCIAValues'] = Relationship(back_populates="lc_stages")
    weighted_results: List['WeightedResults'] = Relationship(back_populates="lc_stages")


class Geographies(SQLModel, table=True):
    geo_id: int = Field(primary_key=True)
    international_code: int
    geo_shorthand_2: str
    geo_shorthand_3: str
    country_name: str = Field()
    normalized_lcis: List['NormalizedLCIAValues'] = Relationship(back_populates="geographies")
    single_scores: List['SingleScores'] = Relationship(back_populates="geographies")
    weighted_results: List['WeightedResults'] = Relationship(back_populates="geographies")


class MetaData(SQLModel, table=True):
    item_id: str = Field(primary_key=True)
    geo_id: int = Field(foreign_key="geographies.geo_id")
    code_ciqual: Optional[str] = Field(default=None)
    name_lci: str
    group_id: Optional[int] = Field(default=None, foreign_key="groups.group_id")
    subgroup_id: Optional[int] = Field(default=None, foreign_key="subgroups.subgroup_id")
    proxy_flag: bool = Field(sa_column=Column(Boolean, nullable=False))
    normalized_lcis: List['NormalizedLCIAValues'] = Relationship(back_populates="meta_data")
    single_scores: List['SingleScores'] = Relationship(back_populates="meta_data")
    weighted_results: List['WeightedResults'] = Relationship(back_populates="meta_data")
    groups: Optional['Groups'] = Relationship(back_populates="meta_data")
    subgroups: Optional['Subgroups'] = Relationship(back_populates="meta_data")


class NormalizedLCIAValues(SQLModel, table=True):
    item_id: str = Field(foreign_key="metadata.item_id", primary_key=True)
    geo_id: int = Field(foreign_key="geographies.geo_id", primary_key=True)
    ic_id: int = Field(foreign_key="impactcategories.ic_id", primary_key=True)
    lc_stage_id: int = Field(foreign_key="lifecyclestages.lc_stage_id", primary_key=True)
    normalized_lcia_value: Optional[float] = Field(default=None)
    non_normalized_lcia_value: Optional[float] = Field(default=None)
    meta_data: MetaData = Relationship(back_populates="normalized_lcis")
    impact_categories: ImpactCategories = Relationship(back_populates="normalized_lcis")
    lc_stages: LifeCycleStages = Relationship(back_populates="normalized_lcis")
    geographies: Geographies = Relationship(back_populates="normalized_lcis")


class WeightingSchemes(SQLModel, table=True):
    scheme_id: int = Field(primary_key=True)
    name: str
    impact_category_weights: List['ImpactCategoryWeights'] = Relationship(back_populates="weighting_schemes")
    single_scores: List['SingleScores'] = Relationship(back_populates="weighting_schemes")
    weighted_results: List['WeightedResults'] = Relationship(back_populates="weighting_schemes")


class ImpactCategoryWeights(SQLModel, table=True):
    scheme_id: int = Field(foreign_key="weightingschemes.scheme_id", primary_key=True)
    ic_id: int = Field(foreign_key="impactcategories.ic_id", primary_key=True)
    ic_weight: float
    weighting_schemes: WeightingSchemes = Relationship(back_populates="impact_category_weights")
    impact_categories: ImpactCategories = Relationship(back_populates="impact_category_weights")


class SingleScores(SQLModel, table=True):
    item_id: str = Field(foreign_key="metadata.item_id", primary_key=True)
    geo_id: int = Field(foreign_key="geographies.geo_id", primary_key=True)
    scheme_id: int = Field(foreign_key="weightingschemes.scheme_id", primary_key=True)
    single_score: Optional[float] = Field(default=None)
    meta_data: MetaData = Relationship(back_populates="single_scores")
    geographies: Geographies = Relationship(back_populates="single_scores")
    weighting_schemes: WeightingSchemes = Relationship(back_populates="single_scores")


class WeightedResults(SQLModel, table=True):
    item_id: str = Field(foreign_key="metadata.item_id", primary_key=True)
    geo_id: int = Field(foreign_key="geographies.geo_id", primary_key=True)
    ic_id: int = Field(foreign_key="impactcategories.ic_id", primary_key=True)
    lc_stage_id: int = Field(foreign_key="lifecyclestages.lc_stage_id", primary_key=True)
    scheme_id: int = Field(foreign_key="weightingschemes.scheme_id", primary_key=True)
    weighted_value: Optional[float] = Field(default=None)
    meta_data: MetaData = Relationship(back_populates="weighted_results")
    geographies: Geographies = Relationship(back_populates="weighted_results")
    impact_categories: ImpactCategories = Relationship(back_populates="weighted_results")
    lc_stages: LifeCycleStages = Relationship(back_populates="weighted_results")
    weighting_schemes: WeightingSchemes = Relationship(back_populates="weighted_results")


class Groups(SQLModel, table=True):
    group_id: int = Field(primary_key=True)
    group_name: str
    meta_data: List['MetaData'] = Relationship(back_populates="groups")


class Subgroups(SQLModel, table=True):
    subgroup_id: int = Field(primary_key=True)
    subgroup_name: str
    meta_data: List['MetaData'] = Relationship(back_populates="subgroups")


if __name__ == "__main__":
    print("Models are ready for use with SQLModel.")
