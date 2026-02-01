from typing import Generator

from anystore.store import get_store
from banal import ensure_dict, ensure_list

from investigraph.model.context import DatasetContext
from investigraph.model.source import Source


def handle(ctx: DatasetContext) -> Generator[Source, None, None]:
    """
    The default handler for the seed stage.

    Args:
        ctx: instance of the current `DatasetContext`

    Yields:
        Generator of `Source` objects for further processing in extract stage.
    """
    if ctx.config.seed.uri is not None:
        store = get_store(ctx.config.seed.uri)
        globs = ensure_list(ctx.config.seed.glob)
        for glob in globs:
            for key in store.iterate_keys(
                glob=glob,
                prefix=ctx.config.seed.prefix,
                exclude_prefix=ctx.config.seed.exclude_prefix,
            ):
                yield Source(
                    uri=store.to_uri(key),
                    **ensure_dict(ctx.config.seed.source_options),
                )
