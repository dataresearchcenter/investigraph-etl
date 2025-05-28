"""
Seed sources for extraction
"""

from typing import Generator

from anystore.store import get_store
from banal import ensure_dict, ensure_list

from investigraph.model.context import DatasetContext
from investigraph.model.source import Source


def handle(ctx: DatasetContext) -> Generator[Source, None, None]:
    if ctx.config.seed.uri is not None:
        store = get_store(ctx.config.seed.uri)
        globs = ensure_list(ctx.config.seed.glob) or [None]
        for glob in globs:
            for key in store.iterate_keys(
                glob=glob,
                prefix=ctx.config.seed.prefix,
                exclude_prefix=ctx.config.seed.exclude_prefix,
            ):
                yield Source(
                    uri=store.get_key(key),
                    **ensure_dict(ctx.config.seed.source_options),
                )
