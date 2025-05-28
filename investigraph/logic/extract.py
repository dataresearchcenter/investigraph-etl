"""
Extract sources to iterate objects to dict records
"""

import numpy as np
from runpandarun import Playbook
from runpandarun.io import guess_handler_from_mimetype

from investigraph.model.context import SourceContext
from investigraph.types import RecordGenerator


def extract_pandas(ctx: SourceContext) -> RecordGenerator:
    play = ctx.source.pandas
    if play is None or play.read is None:
        raise ValueError("No playbook config")
    if play.read.handler is None:
        play.read.handler = f"read_{guess_handler_from_mimetype(ctx.source.mimetype)}"
    with ctx.open() as h:
        play.read.uri = h
        df = play.read.handle()
        for _, row in df.iterrows():
            yield dict(row.replace(np.nan, None))


# entrypoint
def handle(ctx: SourceContext, *args, **kwargs) -> RecordGenerator:
    if ctx.source.pandas is None:
        ctx.source.pandas = Playbook()
    yield from extract_pandas(ctx, *args, **kwargs)
