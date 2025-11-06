from ftmq.io import smart_read_proxies

from investigraph.pipeline import run


def test_pipeline_local(tmp_path, monkeypatch):
    monkeypatch.setenv("INVESTIGRAPH_EXTRACT_CACHE", "0")
    out = run("./tests/fixtures/eu_authorities.local.yml")
    proxies = [p for p in smart_read_proxies(out.entities_uri)]
    assert len(proxies) == 151

    entities_uri = tmp_path / "entities.ftm.json"
    out = run("./tests/fixtures/eu_authorities.local.yml", entities_uri=entities_uri)
    assert out.entities_uri == entities_uri
    proxies = [p for p in smart_read_proxies(entities_uri)]
    assert len(proxies) == 151


# def test_pipeline_from_config():
#     out = run("./tests/fixtures/ec_meetings/config.yml")
#     proxies = [p for p in smart_read_proxies(out.entities_uri)]
#     assert len(proxies) > 50_000


def test_pipeline_local_customized(monkeypatch):
    monkeypatch.setenv("INVESTIGRAPH_EXTRACT_CACHE", "0")
    assert run("./tests/fixtures/eu_authorities.custom.yml")


def test_pipeline_export(tmp_path, monkeypatch):
    monkeypatch.setenv("INVESTIGRAPH_EXTRACT_CACHE", "0")
    entities_uri = tmp_path / "test-entities.ftm.json"
    assert run("./tests/fixtures/eu_authorities.local.yml", entities_uri=entities_uri)
    proxies = [p for p in smart_read_proxies(entities_uri)]
    assert len(proxies) == 151
