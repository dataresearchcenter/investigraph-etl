import pytest

from investigraph import util
from investigraph.exceptions import DataError


def test_util_join():
    assert util.join_text("A", " ", "b", "-") == "A b"


def test_util_str_or_none():
    assert util.str_or_none("foo") == "foo"
    assert util.str_or_none("") is None
    assert util.str_or_none(" ") is None
    assert util.str_or_none(None) is None


def test_util_make_entity():
    proxy = util.make_entity("LegalEntity")
    assert proxy.id is None
    with pytest.raises(DataError):
        util.make_entity("LegalEntity", name="test")
    proxy = util.make_entity("Person", id="i", name="Jane", country="France")
    assert proxy.id == "i"
    assert "Jane" in proxy.get("name")
    assert proxy.caption == "Jane"
    assert proxy.first("country") == "fr"
