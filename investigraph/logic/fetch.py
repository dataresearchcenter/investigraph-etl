"""Fetch remote files (e.g. PDFs), store in archive and get Document entities
back to work with"""

from functools import cache

from anystore.types import SDict
from anystore.util import join_uri
from banal import ensure_dict
from ftm_lakehouse import get_archive as get_lakehouse_archive
from ftm_lakehouse.model import File
from ftm_lakehouse.repository import ArchiveRepository
from memorious.logic.fetch import create_fetch_client

from investigraph.settings import Settings


@cache
def get_archive(dataset: str) -> ArchiveRepository:
    settings = Settings()
    # use configured lakehouse uri or fall back to data_root
    uri = join_uri(settings.lakehouse_uri or settings.data_root, dataset)
    return get_lakehouse_archive(dataset, uri)


def fetch_file(
    dataset: str,
    url: str,
    cache_key: str | None = None,
    fetch_options: SDict | None = None,
    **extra_data,
) -> File:
    """
    Retrieve a remote file via http. Uses `memorious.logic.fetch` module for
    internal caching. If the remote source didn't change, it is not re-fetched.
    Stores the bytes content in the configured `LAKEHOUSE_URI` or `DATA_ROOT`
    for the given dataset.

    Args:
        dataset: Investigraph dataset
        url: Remote url to fetch
        cache_key: Cache key to use for incremental skipping
        fetch_options: Pass through kwargs to `memorious.logic.fetch.fetch`
        extra_data: Extra properties or metadata to store at the `File` object.
    """
    with create_fetch_client(dataset=dataset) as client:
        tag = client.context.make_key(f"fetch_file/{cache_key}")
        if cache_key and client.context.check_incremental(cache_key):
            file = client.context.tags.get(tag, model=File)
            if file is not None:
                return file
        archive = get_archive(dataset)
        res = client.get(url, **ensure_dict(fetch_options))
        assert res is not None
        file = archive.store(url, checksum=res.content_hash, **extra_data)
        if cache_key:
            client.context.mark_incremental(cache_key)
            client.context.tags.put(tag, file, model=File)
        return file
