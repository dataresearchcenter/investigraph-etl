from typing import TYPE_CHECKING, Iterable

from followthemoney import StatementEntity

if TYPE_CHECKING:
    from investigraph.model import DatasetContext


def handle(ctx: "DatasetContext", proxies: Iterable[StatementEntity]) -> int:
    """
    The default handler for the load stage. It writes the given proxies to the
    configured store.

    Args:
        ctx: instance of the current runtime `DatasetContext`
        proxies: Iterable of `StatementEntity`

    Returns:
        The number of entities written to the store.
    """
    ix = 0
    with ctx.store.writer() as bulk:
        for proxy in proxies:
            bulk.add_entity(proxy)
            ix += 1
    return ix
