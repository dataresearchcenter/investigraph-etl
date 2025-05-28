from typing import TYPE_CHECKING, Any, Callable, ClassVar, TypeAlias

from anystore.types import Uri
from anystore.util import pydantic_merge
from banal import ensure_list, keys_values
from pydantic import BaseModel
from runpandarun import Playbook

from investigraph.model.mapping import QueryMapping
from investigraph.settings import Settings
from investigraph.util import get_func

if TYPE_CHECKING:
    from investigraph.model.context import SourceContext, DatasetContext

from investigraph.model.source import Source

settings = Settings()

CTX: TypeAlias = "SourceContext | DatasetContext"


class Stage(BaseModel):
    default_handler: ClassVar[str] = ""
    handler: str = ""

    def __init__(self, **data):
        data["handler"] = data.pop("handler", self.default_handler)
        super().__init__(**data)

    def get_handler(self) -> Callable:
        return get_func(self.handler)

    def handle(self, ctx: CTX, *args, **kwargs) -> Any:
        handler = self.get_handler()
        return handler(ctx, *args, **kwargs)


class SeedStage(Stage):
    default_handler = settings.seeder

    uri: str | None = None
    prefix: str | None = None
    exclude_prefix: str | None = None
    glob: str | list[str] | None = None
    storage_options: dict[str, Any] | None = None
    source_options: dict[str, Any] | None = None


class ExtractStage(Stage):
    default_handler = settings.extractor

    archive: bool = True
    sources: list[Source] = []
    pandas: Playbook = Playbook()

    def __init__(self, **data):
        super().__init__(**data)
        for source in self.sources:
            if source.pandas is not None:
                source.pandas = pydantic_merge(self.pandas, source.pandas)
            else:
                source.pandas = source.pandas or self.pandas


class TransformStage(Stage):
    default_handler = settings.transformer

    queries: list[QueryMapping] = []

    def __init__(self, **data):
        data["queries"] = ensure_list(keys_values(data, "queries", "query"))
        super().__init__(**data)


class LoadStage(Stage):
    default_handler = settings.loader

    uri: str = settings.store_uri


class ExportStage(Stage):
    default_handler = settings.exporter

    index_uri: Uri | None = None
    entities_uri: Uri | None = None
