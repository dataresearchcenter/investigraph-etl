from typing import Any

from investigraph.logic.extract import extract_pandas
from investigraph.model import Config
from investigraph.model.context import DatasetContext, SourceContext


def _get_records(ctx: SourceContext) -> list[dict[str, Any]]:
    return [r for r in extract_pandas(ctx)]


def test_extract(ec_meetings_local: Config, gdho: Config):
    tested = False
    ctx = DatasetContext(config=ec_meetings_local)
    for source in ctx.get_sources():
        records = _get_records(source)
        assert len(records) == 12482
        for rec in records:
            assert isinstance(rec, dict)
            assert "Location" in rec.keys()
            tested = True
            break
    assert tested

    tested = False
    ctx = DatasetContext(config=gdho)
    for source in ctx.get_sources():
        records = _get_records(source)
        assert len(records) == 997
        for rec in records:
            assert isinstance(rec, dict)
            assert "Name" in rec.keys()
            tested = True
            break
    assert tested
