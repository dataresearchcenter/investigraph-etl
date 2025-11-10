"""
Extract sources to iterate objects to dict records
"""

import numpy as np
from runpandarun import Playbook
from runpandarun.io import guess_handler_from_mimetype

from investigraph.exceptions import ImproperlyConfigured
from investigraph.model.context import SourceContext
from investigraph.types import RecordGenerator


def extract_pandas(ctx: SourceContext) -> RecordGenerator:
    play = ctx.source.pandas
    if play is None:
        raise ImproperlyConfigured("No playbook config")
    play = play.model_copy(deep=True)
    if play.read is None:
        raise ImproperlyConfigured("No playbook config")
    if play.read.handler is None:
        play.read.handler = f"read_{guess_handler_from_mimetype(ctx.source.mimetype)}"
    with ctx.open() as h:
        play.read.uri = h
        df = play.run()
        for _, row in df.iterrows():
            yield dict(row.replace(np.nan, None))


# entrypoint
def handle(ctx: SourceContext, *args, **kwargs) -> RecordGenerator:
    """
    The default handler for the extract stage. It handles tabular sources with
    `pandas`. Custom extract handlers must follow this function signature.

    Args:
        ctx: instance of the current `SourceContext`

    Yields:
        Generator of dictionaries `dict[str, Any]` that are the extracted records.
    """
    if ctx.source.pandas is None:
        ctx.source.pandas = Playbook()
    yield from extract_pandas(ctx, *args, **kwargs)
