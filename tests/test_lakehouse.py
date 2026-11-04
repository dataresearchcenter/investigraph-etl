import json
from datetime import date

import pytest
from banal import hash_data
from ftm_lakehouse import get_archive, get_entities
from memorious.core import get_tags
from memorious.operations.store import META_PREFIX

from investigraph import pipeline
from investigraph.logic import fetch
from investigraph.model.config import get_config

URL = "http://localhost:8000/all-authorities.csv"


@pytest.fixture
def lakehouse(monkeypatch, tmp_path):
    monkeypatch.setenv("LAKEHOUSE_URI", str(tmp_path))
    fetch.get_archive.cache_clear()
    get_tags.cache_clear()
    yield tmp_path
    fetch.get_archive.cache_clear()
    get_tags.cache_clear()


def test_lakehouse_pipeline(lakehouse, fixtures_path):
    uri = fixtures_path / "gdho" / "config.local.yml"
    config = get_config(uri)
    pipeline.run(uri)

    entities = list(get_entities(config.dataset.name).query())
    assert len(entities) > 0
    assert (lakehouse / config.dataset.name / "entities.ftm.json").exists()


def test_fetch_file(lakehouse):
    checksum = fetch.fetch_file("test_fetch", URL)
    assert get_archive("test_fetch").exists(checksum)
    assert fetch.fetch_file("test_fetch", URL) == checksum


def test_fetch_file_incremental(lakehouse, monkeypatch):
    checksum = fetch.fetch_file("test_fetch", URL, cache_key="key")

    def fail(*args):
        raise AssertionError("Should be skipped")

    with monkeypatch.context() as patch:
        patch.setattr(fetch, "get_archive", fail)
        assert fetch.fetch_file("test_fetch", URL, cache_key="key") == checksum


def test_fetch_file_metadata(lakehouse):
    checksum = fetch.fetch_file(
        "test_fetch", URL, cache_key="key", title="Authorities", date=date(2026, 1, 1)
    )
    path = f"{META_PREFIX}/{hash_data('key')}.json"
    meta = json.loads(get_archive("test_fetch").get_data(checksum, path))
    assert meta["url"] == meta["sourceUrl"] == URL
    assert meta["content_hash"] == checksum
    assert meta["name"] == meta["key"] == "all-authorities.csv"
    assert meta["mimetype"] == "text/csv"
    assert meta["title"] == "Authorities"
    assert meta["date"] == "2026-01-01"

    # extra data takes precedence
    fetch.fetch_file("test_fetch", URL, cache_key="other", name="other.csv")
    path = f"{META_PREFIX}/{hash_data('other')}.json"
    meta = json.loads(get_archive("test_fetch").get_data(checksum, path))
    assert meta["name"] == "other.csv"
