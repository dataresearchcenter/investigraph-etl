"""Fetch remote files (e.g. PDFs), store in archive and get Document entities
back to work with"""

from functools import cache

from anystore.types import SDict
from anystore.util import join_uri
from banal import ensure_dict
from ftm_lakehouse import get_archive as get_lakehouse_archive
from ftm_lakehouse.model import File
from ftm_lakehouse.repository import ArchiveRepository
from memorious.logic.fetch import fetch

from investigraph.settings import Settings


@cache
def get_archive(dataset: str) -> ArchiveRepository:
    settings = Settings()
    # use configured lakehouse uri or fall back to data_root
    uri = join_uri(settings.lakehouse_uri or settings.data_root, dataset)
    return get_lakehouse_archive(dataset, uri)


def fetch_file(
    dataset: str, url: str, fetch_options: SDict | None = None, **extra_data
) -> File:
    """
    Retrieve a remote file via http. Uses `memorious.logic.fetch` module for
    internal caching. If the remote source didn't change, it is not re-fetched.
    Stores the bytes content in the configured `LAKEHOUSE_URI` or `DATA_ROOT`
    for the given dataset.

    Args:
        dataset: Investigraph dataset
        url: Remote url to fetch
        fetch_options: Pass through kwargs to `memorious.logic.fetch.fetch`
        extra_data: Extra properties or metadata to store at the `File` object.
    """
    archive = get_archive(dataset)
    res = fetch(url, dataset=dataset, **ensure_dict(fetch_options))
    return archive.store(url, checksum=res.content_hash, **extra_data)
