from functools import cache

from anystore.store import BaseStore
from anystore.store.virtual import open_virtual
from anystore.util import make_data_checksum

from investigraph.model.source import Source
from investigraph.settings import Settings


@cache
def get_runtime_cache() -> BaseStore:
    settings = Settings()
    return settings.cache.to_store()


@cache
def get_archive_cache(prefix: str | None = ".cache") -> BaseStore:
    settings = Settings()
    archive_cache = settings.archive.model_copy()
    archive_cache.uri = f"{archive_cache.uri}/{prefix or '.cache'}"
    return archive_cache.to_store()


def make_cache_key(url: str, *args, **kwargs) -> str | None:
    kwargs.pop("delay", None)
    kwargs.pop("stealthy", None)
    kwargs.pop("timeout", None)
    if kwargs.pop("cache", None) is False:
        return
    if not kwargs.pop("url_key_only", False):
        source = Source(uri=url)
        info = source.info()
        if info.cache_key:
            return make_data_checksum((url, info.cache_key, *args, kwargs))
        if kwargs.pop("use_checksum", True):
            with open_virtual(url) as fh:
                return fh.checksum
        return make_data_checksum((url, info.model_dump_json(), *args, kwargs))
    return make_data_checksum((url, *args, kwargs))


def skip_cached_source(source: Source) -> str | None:
    key = make_cache_key(source.uri, use_checksum=True)
    if key:
        cache = get_archive_cache()
        if cache.exists(key):
            return key
