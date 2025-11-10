from typing import TYPE_CHECKING

from anystore.types import Uri
from followthemoney import StatementEntity
from ftmq.types import StatementEntities

from investigraph.model.context import get_source_context
from investigraph.model.mapping import QueryMapping

if TYPE_CHECKING:
    from investigraph.model import SourceContext

from ftmq.util import make_entity

from investigraph.types import Record


def map_record(
    record: Record, mapping: QueryMapping, dataset: str | None = "default"
) -> StatementEntities:
    _mapping = mapping.get_mapping()
    if _mapping.source.check_filters(record):
        entities = _mapping.map(record)
        for proxy in entities.values():
            # Use new ftmq API: make_entity(data, entity_type, default_dataset)
            yield make_entity(proxy.to_dict(), StatementEntity, dataset)


def map_ftm(ctx: "SourceContext", record: Record, ix: int) -> StatementEntities:
    """
    The default handler for the transform stage. It takes a
    [Mapping](https://followthemoney.tech/docs/mappings/) and executes it on
    each incoming record.

    Args:
        ctx: instance of the current `SourceContext`
        record: The record to transform, it is an arbitrary `dict[str, Any]`
        ix: The 1-based index of this record (e.g. line number of the extracted
            source)

    Yields:
        Generator of `StatementEntity` instances
    """
    for mapping in ctx.config.transform.queries:
        yield from map_record(record, mapping, ctx.config.dataset.name)


def transform_record(config_uri: Uri, record: Record, ix: int) -> StatementEntities:
    sctx = get_source_context(config_uri, record.pop("__source__"))
    yield from sctx.config.transform.handle(sctx, record, ix)
