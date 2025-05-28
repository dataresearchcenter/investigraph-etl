from followthemoney.proxy import EntityProxy

from investigraph.logic.export import proxy_merge
from investigraph.model import Source, SourceContext, TaskContext
from investigraph.settings import VERSION as __version__

# FIXME overwrite legacy merge with our downgrading merge for ftmstore:
EntityProxy.merge = proxy_merge

__all__ = [
    "__version__",
    "SourceContext",
    "TaskContext",
    "Source",
]
