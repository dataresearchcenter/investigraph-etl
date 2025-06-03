"""
aggregate fragments to export
"""

from typing import TYPE_CHECKING

from anystore import smart_write
from followthemoney.proxy import E
from ftmq.aggregate import merge
from ftmq.io import smart_write_proxies
from ftmq.model import Dataset
from ftmq.model.coverage import Collector
from ftmq.types import CE
from ftmq.util import make_proxy

if TYPE_CHECKING:
    from investigraph.model import DatasetContext

from investigraph.types import CEGenerator


def proxy_merge(self: E, other: E) -> CE:
    """
    Used to override `EntityProxy.merge` in `investigraph.__init__.py`
    """
    return merge(
        make_proxy(self.to_dict()), make_proxy(other.to_dict()), downgrade=True
    )


def get_iterator(proxies: CEGenerator, collector: Collector) -> CEGenerator:
    for proxy in proxies:
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
