import csv
import sys

import orjson
from anystore import smart_open

from investigraph.model import Source, SourceContext

URL = "http://localhost:8000/all-authorities.csv"


def seed(ctx: SourceContext):
    yield Source(uri=URL, name="all-authorities-csv")


def extract(ctx: SourceContext, *args, **kwargs):
    with smart_open(URL, mode="r") as h:
        reader = csv.DictReader(h)
        yield from reader


def load(ctx, proxies, *args, **kwargs):
    for proxy in proxies:
        sys.stdout.write(orjson.dumps(proxy.to_dict()).decode())
        return
