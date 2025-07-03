from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# Auto-generated SQLModel classes from FIT_eeb3795.db schema
# Generated on: 2025-07-08

class Geographies(SQLModel, table=True):
    __tablename__ = "geographies"
    geo_id: int = Field(primary_key=True)
    international_code: int = Field()
    geo_shorthand_2: str = Field()
    geo_shorthand_3: str = Field()
    country_name: str = Field()

class Groups(SQLModel, table=True):
    __tablename__ = "groups"
    group_id: int = Field(primary_key=True)
    group_name: str = Field()

class Impactcategories(SQLModel, table=True):
    __tablename__ = "impactcategories"
    ic_id: int = Field(primary_key=True)
    ic_name: str = Field()
    ic_shorthand: str = Field()
    normalization_value: float = Field()
    normalization_unit: str = Field()

class Impactcategoryweights(SQLModel, table=True):
    __tablename__ = "impactcategoryweights"
    scheme_id: int = Field(primary_key=True)
    ic_id: int = Field(primary_key=True)
    ic_weight: float = Field()

class Lifecyclestages(SQLModel, table=True):
    __tablename__ = "lifecyclestages"
    lc_stage_id: int = Field(primary_key=True)
    lc_stage_shorthand: str = Field()
    lc_name: str = Field()

class Metadata(SQLModel, table=True):
    __tablename__ = "metadata"
    item_id: str = Field(primary_key=True)
    geo_id: int = Field(primary_key=True)
    code_ciqual: Optional[str] = Field(default=None)
    name_lci: str = Field()
    group_id: Optional[int] = Field(default=None)
    subgroup_id: Optional[int] = Field(default=None)
    proxy_flag: str = Field()

class Normalizedlciavalues(SQLModel, table=True):
    __tablename__ = "normalizedlciavalues"
    item_id: str = Field(primary_key=True)
    geo_id: int = Field(primary_key=True)
    ic_id: int = Field(primary_key=True)
    lc_stage_id: int = Field(primary_key=True)
    normalized_lcia_value: Optional[float] = Field(default=None)
    non_normalized_lcia_value: Optional[float] = Field(default=None)

class Singlescores(SQLModel, table=True):
    __tablename__ = "singlescores"
    item_id: str = Field(primary_key=True)
    geo_id: int = Field(primary_key=True)
    scheme_id: int = Field(primary_key=True)
    single_score: Optional[float] = Field(default=None)

class Subgroups(SQLModel, table=True):
    __tablename__ = "subgroups"
    subgroup_id: int = Field(primary_key=True)
    subgroup_name: str = Field()

class Weightedresults(SQLModel, table=True):
    __tablename__ = "weightedresults"
    item_id: str = Field(primary_key=True)
    geo_id: int = Field(primary_key=True)
    ic_id: int = Field(primary_key=True)
    lc_stage_id: int = Field(primary_key=True)
    scheme_id: int = Field(primary_key=True)
    weighted_value: Optional[float] = Field(default=None)

class Weightingschemes(SQLModel, table=True):
    __tablename__ = "weightingschemes"
    scheme_id: int = Field(primary_key=True)
    name: str = Field()

