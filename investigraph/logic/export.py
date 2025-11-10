"""
aggregate fragments to export
"""

from typing import TYPE_CHECKING

from anystore import smart_write
from anystore.io import logged_items
from anystore.logging import get_logger
from followthemoney import StatementEntity
from followthemoney.proxy import E
from ftmq.aggregate import merge
from ftmq.io import smart_write_proxies
from ftmq.model import Dataset
from ftmq.model.stats import Collector
from ftmq.types import StatementEntities
from ftmq.util import make_entity

if TYPE_CHECKING:
    from investigraph.model import DatasetContext

log = get_logger(__name__)


def proxy_merge(self: E, other: E) -> E:
    """
    Used to override `EntityProxy.merge` in `investigraph.__init__.py`
    """
    return merge(
        make_entity(self.to_dict(), StatementEntity),
        make_entity(other.to_dict(), StatementEntity),
        downgrade=True,
    )


def get_iterator(proxies: StatementEntities, collector: Collector) -> StatementEntities:
    for proxy in logged_items(proxies, "Export", item_name="Proxy", logger=log):
        collector.collect(proxy)
        yield proxy


def handle(ctx: "DatasetContext", *args, **kwargs) -> Dataset:
    """
    The default handler of the export stage. It iterates through the entities
    store, calculates dataset statistics and writes the entities and dataset
    index to json files.

    If neither `entities_uri` or `index_uri` is set, no stats for the `Dataset`
    are computed.

    Args:
        ctx: The current runtime `DatasetContext`

    Returns:
        The `Dataset` object with calculated statistics.
    """
    collector = Collector()
    proxies = ctx.store.iterate(dataset=ctx.dataset)
    iterator = get_iterator(proxies, collector)
    if ctx.config.export.entities_uri:
        smart_write_proxies(ctx.config.export.entities_uri, iterator)
    elif ctx.config.export.index_uri:
        # still compute statistics by iterating through the proxy iterator
        _ = [p for p in iterator]

    if ctx.config.export.index_uri:
        stats = collector.export()
        ctx.config.dataset.apply_stats(stats)
        smart_write(
            ctx.config.export.index_uri, ctx.config.dataset.model_dump_json().encode()
        )

    return ctx.config.dataset
