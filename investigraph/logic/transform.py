"""
Transform stage: map data records to ftm proxies
"""

from typing import TYPE_CHECKING

from anystore.types import Uri

from investigraph.model.context import get_source_context
from investigraph.model.mapping import QueryMapping

if TYPE_CHECKING:
    from investigraph.model import SourceContext

from ftmq.util import make_proxy

from investigraph.types import CEGenerator, Record


def map_record(
    record: Record, mapping: QueryMapping, dataset: str | None = "default"
) -> CEGenerator:
    _mapping = mapping.get_mapping()
    if _mapping.source.check_filters(record):
        entities = _mapping.map(record)
        for proxy in entities.values():
            yield make_proxy(proxy.to_dict(), dataset=dataset)


def map_ftm(ctx: "SourceContext", record: Record, ix: int) -> CEGenerator:
    for mapping in ctx.config.transform.queries:
        yield from map_record(record, mapping, ctx.config.dataset.name)


def transform_record(config_uri: Uri, record: Record, ix: int) -> CEGenerator:
    sctx = get_source_context(config_uri, record.pop("__source__"))
    yield from sctx.config.transform.handle(sctx, record, ix)
