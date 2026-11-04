"""Fetch remote files (e.g. PDFs), store in archive and get Document entities
back to work with"""

from functools import cache
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from anystore.logic.serialize import to_store
from anystore.types import SDict
from anystore.util import join_uri
from banal import ensure_dict, hash_data
from ftm_lakehouse import get_archive as get_lakehouse_archive
from ftm_lakehouse.repository import ArchiveRepository
from memorious.logic.fetch import create_fetch_client
from memorious.operations.store import META_PREFIX

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
) -> str:
    """
    Retrieve a remote file via http. Uses `memorious.logic.fetch` module for
    internal caching. If the remote source didn't change, it is not re-fetched.
    Stores the bytes content in the configured `LAKEHOUSE_URI` or `DATA_ROOT`
    for the given dataset, with its metadata as json next to the blob (same
    layout as the `memorious.operations.store.lakehouse` operation).

    Args:
        dataset: Investigraph dataset
        url: Remote url to fetch
        cache_key: Cache key to use for incremental skipping
        fetch_options: Pass through kwargs to `memorious.logic.fetch.fetch`
        extra_data: Extra properties or metadata to store next to the file.

    Returns:
        The checksum of the file in the archive
    """
    with create_fetch_client(dataset=dataset) as client:
        tag = client.context.make_key(f"fetch_checksum/{cache_key}")
        if cache_key and client.context.check_incremental(cache_key):
            checksum = client.context.tags.get(tag)
            if checksum is not None:
                return checksum
        archive = get_archive(dataset)
        res = client.get(url, **ensure_dict(fetch_options))
        assert res is not None
        checksum = archive.store(url, checksum=res.content_hash)
        key = unquote(urlparse(url).path).strip("/")
        meta = {
            **res.serialize(),
            "sourceUrl": url,
            "name": res.file_name or PurePosixPath(key).name,
            "key": key,
            "mimetype": res.content_type,
            **extra_data,
        }
        # one file per source, as the same blob can have many sources
        meta_path = f"{META_PREFIX}/{hash_data(cache_key or res.request_id)}.json"
        archive.put_data(checksum, meta_path, to_store(meta, "json"))
        if cache_key:
            client.context.mark_incremental(cache_key)
            client.context.tags.put(tag, checksum)
        return checksum
