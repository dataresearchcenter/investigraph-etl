from datetime import datetime

from anystore.model import Stats
from rigour.mime.types import CSV, XLSX

from investigraph.model import Config


def test_source(eu_authorities: Config, ec_meetings_local: Config):
    for source in ec_meetings_local.extract.sources:
        info = source.info()
        assert isinstance(info, Stats)
        assert isinstance(info.updated_at, datetime)
        assert info.mimetype == XLSX
        break

    for source in eu_authorities.extract.sources:
        info = source.info()
        assert isinstance(info.updated_at, datetime)
        assert info.mimetype == CSV
        break
