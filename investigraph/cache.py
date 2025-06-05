from functools import cache

from anystore.logging import get_logger
from anystore.store import BaseStore
from anystore.store.virtual import open_virtual
from anystore.types import Uri
from anystore.util import make_data_checksum

from investigraph.model.source import Source
from investigraph.settings import Settings

log = get_logger(__name__)


@cache
def get_runtime_cache() -> BaseStore:
    """
    Get shared runtime cache. This should be a fast key-value store that doesn't
    need to be persistent.

    Set via `INVESTIGRAPH_CACHE_URI` (see [Settings][investigraph.settings])

    Returns:
        The runtime cache store (see
            [anystore](https://docs.investigraph.dev/lib/anystore))
    """
    settings = Settings()
    return settings.cache.to_store()


@cache
def get_archive_cache(prefix: str | None = ".cache") -> BaseStore:
    """
    Get the archive cache subfolder where to store persistent state about
    sources

    Set the base archive via `INVESTIGRAPH_ARCHIVE_URI` (see
    [Settings][investigraph.settings])

    Returns:
        The archive cache store (see
            [anystore](https://docs.investigraph.dev/lib/anystore))
    """
    settings = Settings()
    archive_cache = settings.archive.model_copy()
    archive_cache.uri = f"{archive_cache.uri}/{prefix or '.cache'}"
    return archive_cache.to_store()


def make_cache_key(uri: Uri, *args, **kwargs) -> str | None:
    """
    Compute a cache key for the given uri. This tries to get an `etag` or
    `last-modified` header, or optionally falls back to computing a checksum or
    a key just by the `uri`.

    Args:
        uri: The local or remote uri for the file
        cache: `bool` if to use cache at all (default)
        url_key_only: `bool` if to compute cache key just by uri as fallback
            (default `False`)
        use_checksum: `bool` if to compute the checksum as fallback (default
            `False`)
        checksum: `str`: Give an already pre-computed checksum when using
            `use_checksum` (optional)
    """
    kwargs.pop("delay", None)
    kwargs.pop("stealthy", None)
    kwargs.pop("timeout", None)
    if kwargs.pop("cache", None) is False:
        return
    if not kwargs.pop("url_key_only", False):
        source = Source(uri=uri)
        info = source.info()
        if info.cache_key:
            return make_data_checksum((uri, info.cache_key, *args, kwargs))
        if kwargs.pop("use_checksum", True):
            if "checksum" in kwargs:
                return kwargs["checksum"]
            try:
                with open_virtual(uri) as fh:
                    return fh.checksum
            except Exception as e:
                log.warn(
                    f"Cannot calculate checksum: `{e.__class__.__name__}`: {e}",
                    uri=uri,
                    **kwargs,
                )
        return make_data_checksum((uri, info.model_dump_json(), *args, kwargs))
    return make_data_checksum((uri, *args, kwargs))
