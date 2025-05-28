"""
# Archive

Simple archive implementation for storing scraped files based on `anystore`
"""

import random
import time
from functools import cache
from typing import IO, AnyStr, ContextManager
from urllib.parse import urlsplit

from anystore import anycache
from anystore.logging import get_logger
from anystore.store import BaseStore
from anystore.store.virtual import open_virtual
from anystore.types import Uri
from anystore.util import join_relpaths, make_data_checksum

from investigraph.model.source import Source
from investigraph.settings import Settings

settings = Settings()


@cache
def get_archive(uri: Uri | None = None) -> BaseStore:
    archive = settings.archive.model_copy()
    archive.uri = uri or archive.uri
    return archive.to_store()


@cache
def get_archive_cache(prefix: str | None = ".cache") -> BaseStore:
    archive_cache = settings.archive.model_copy()
    archive_cache.uri = f"{archive_cache.uri}/{prefix or '.cache'}"
    return archive_cache.to_store()


def make_archive_key(uri: Uri) -> str:
    return join_relpaths(*urlsplit(str(uri))[1:])


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
        return make_data_checksum((url, info.model_dump_json(), *args, kwargs))
    return make_data_checksum((url, *args, kwargs))


@anycache(key_func=make_cache_key, store=get_archive_cache())
def archive_source(
    uri: Uri,
    *args,
    url_key_only: bool | None = False,
    cache: bool | None = True,
    stealthy: bool | None = False,
    delay: int | None = None,
    raise_on_error: bool | None = True,
    **kwargs,
) -> str:
    """
    Archive a remote file and return the local archive key
    """
    if stealthy:
        kwargs["headers"] = kwargs.pop("headers", {})
        kwargs["headers"]["User-Agent"] = random.choice(AGENTS)
    if delay is not None:
        time.sleep(delay)
    log = get_logger(__name__)
    archive = get_archive()
    key = make_archive_key(uri)
    log.info(f"ARCHIVING {uri} ...", archive=archive.uri, prefix=key)
    try:
        with open_virtual(uri, backend_config=kwargs) as fh:
            key = f"{key}/{fh.checksum}"
            with archive.open(key, "wb") as out:
                out.write(fh.read())
    except Exception as e:
        if raise_on_error:
            raise e
        log.error(str(e))
    return str(key)


def open(
    url: str,
    url_key_only: bool | None = False,
    cache: bool | None = True,
    stealthy: bool | None = False,
    delay: int | None = None,
    raise_on_error: bool | None = True,
    mode: str | None = None,
    **kwargs,
) -> ContextManager[IO[AnyStr]]:
    key = archive_source(
        url,
        cache=cache,
        stealthy=stealthy,
        delay=delay,
        raise_on_error=raise_on_error,
        url_key_only=url_key_only,
        **kwargs,
    )
    archive = get_archive()
    return archive.open(key, mode=mode)


# https://www.useragents.me/#most-common-desktop-useragents-json-csv
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.4",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 OPR/95.0.0.",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.",  # noqa: B950
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.10",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Geck",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 OPR/95.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.3",  # noqa: B950
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.3",  # noqa: B950
]
