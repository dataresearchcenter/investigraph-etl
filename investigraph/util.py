import re
from functools import cache
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Callable

from anystore.types import SDict, Uri
from anystore.util import make_data_checksum
from banal import ensure_dict
from followthemoney import StatementEntity
from followthemoney.util import join_text as _join_text
from ftmq.util import (
    clean_name,
    make_dataset,
    make_fingerprint,
    make_fingerprint_id,
    make_string_id,
)
from normality import slugify

from investigraph.exceptions import DataError


def slugified_dict(data: dict[Any, Any]) -> SDict:
    return {str(slugify(k, "_")): v for k, v in ensure_dict(data).items()}


def make_entity(
    schema: str,
    id: str | None = None,
    dataset: str | None = None,
    **properties,
) -> StatementEntity:
    if properties and not id:
        raise DataError("Specify Entity ID when using properties kwargs!")

    entity = StatementEntity.from_dict(
        {"id": id, "schema": schema}, default_dataset=make_dataset(dataset)
    )
    # add the property values via this api to ensure type checking & cleaning
    for k, v in properties.items():
        entity.add(k, v)
    return entity


module_re = re.compile(r"^[\w\.]+:[\w]+")


@cache
def is_module(path: str) -> bool:
    return bool(module_re.match(path))


@cache
def get_func(path: Uri, base_path: Uri | None = None) -> Callable:
    if base_path:
        path = Path(str(base_path)) / Path(str(path))
    module, func = str(path).rsplit(":", 1)
    if is_module(str(path)):
        module = import_module(module)
    else:
        mpath = Path(module)
        spec = spec_from_file_location(mpath.stem, module)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load `{mpath}`")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
    return getattr(module, func)


def str_or_none(value: Any) -> str | None:
    if not value:
        return None
    value = str(value).strip()
    return value or None


def join_text(*parts: Any, sep: str = " ") -> str | None:
    return _join_text(*[clean_name(p) for p in parts], sep=sep)


def to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return ensure_dict(obj)


__all__ = [
    "make_string_id",
    "make_fingerprint",
    "make_fingerprint_id",
    "make_entity",
    "make_data_checksum",
    "str_or_none",
    "join_text",
    "clean_name",
]
