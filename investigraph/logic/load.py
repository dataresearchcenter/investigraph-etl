"""
Load transformed data (proxy fragments) to a nomenklatura statement store
"""

from typing import TYPE_CHECKING, Iterable, TypeAlias

from nomenklatura.entity import CE

from investigraph.types import SDict

if TYPE_CHECKING:
    from investigraph.model import DatasetContext

TProxies: TypeAlias = Iterable[SDict]


def handle(ctx: "DatasetContext", proxies: Iterable[CE]) -> int:
    ix = 0
    with ctx.store.writer() as bulk:
        for proxy in proxies:
            bulk.add_entity(proxy)
            ix += 1
    return ix
