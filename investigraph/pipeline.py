"""
The main entrypoint for running a dataset config
"""

from datetime import datetime

from anystore.types import Uri
from pydantic import BaseModel

from investigraph.model.config import Config, get_config
from investigraph.model.context import DatasetContext


class WorkflowRun(BaseModel):
    """
    Defines a workflow run
    """

    config: Config
    start: datetime
    end: datetime
    entities_uri: Uri | None
    index_uri: Uri | None
    statistics_uri: Uri | None


def run(
    config_uri: Uri,
    store_uri: Uri | None = None,
    entities_uri: Uri | None = None,
    index_uri: Uri | None = None,
    statistics_uri: Uri | None = None,
) -> WorkflowRun:
    start = datetime.now()
    config = get_config(config_uri)
    config.load.uri = store_uri or config.load.uri
    config.export.index_uri = index_uri or config.export.index_uri
    config.export.entities_uri = entities_uri or config.export.entities_uri
    config.export.statistics_uri = entities_uri or config.export.statistics_uri
    ctx = DatasetContext(config=config)

    has_run = False  # if all sources are cached
    for sctx in ctx.get_sources():
        records = sctx.extract()
        proxies = sctx.transform(records)
        sctx.load(proxies)
        has_run = True

    if has_run:
        ctx.export()
    else:
        ctx.log.info("No data exported as all sources are cached.")

    end = datetime.now()
    return WorkflowRun(
        start=start,
        end=end,
        config=config,
        entities_uri=config.export.entities_uri,
        index_uri=config.export.index_uri,
        statistics_uri=config.export.statistics_uri,
    )
