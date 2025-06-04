from functools import cache

from anystore.store import BaseStore

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
