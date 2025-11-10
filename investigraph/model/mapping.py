from functools import cache
from typing import TypeAlias

from followthemoney import model
from followthemoney.mapping.query import QueryMapping as _QueryMapping
from pydantic import BaseModel, Field

# Type aliases for schema and property names (strings)
Schemata: TypeAlias = str
Properties: TypeAlias = str


class PropertyMapping(BaseModel):
    column: str | None = None
    columns: list[str] | None = None
    join: str | None = None
    split: str | None = None
    entity: str | None = None
    format: str | None = None
    fuzzy: str | None = None
    required: bool | None = False
    literal: str | None = None
    literals: list[str] | None = None
    template: str | None = None


class EntityMapping(BaseModel):
    key: str | None = None
    keys: list[str] | None = []
    key_literal: str | None = None
    id_column: str | None = None
    schema_: Schemata = Field(..., alias="schema")
    properties: dict[Properties, PropertyMapping] = {}


class QueryMapping(BaseModel):
    entities: dict[str, EntityMapping] | None = {}
    filters: dict[str, str] | None = {}
    filters_not: dict[str, str] | None = {}

    def get_mapping(self) -> _QueryMapping:
        return load_mapping(self)

    def __hash__(self) -> int:
        return hash(repr(self.model_dump()))


@cache
def load_mapping(mapping: QueryMapping) -> _QueryMapping:
    mapping_data = mapping.model_dump(by_alias=True)
    mapping_data.pop("database", None)
    mapping_data["csv_url"] = "/dev/null"
    return model.make_mapping(mapping_data)
