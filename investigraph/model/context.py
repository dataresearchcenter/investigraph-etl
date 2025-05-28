from functools import cache
from typing import IO, Any, AnyStr, ContextManager, Generator

from anystore import smart_open
from anystore.io import Uri, get_logger, logged_items
from anystore.store import BaseStore
from followthemoney.util import make_entity_id
from ftmq.aggregate import merge
from ftmq.model import DatasetStats
from ftmq.store import Store, get_store
from ftmq.util import join_slug, make_fingerprint_id
from nomenklatura.entity import CE, CompositeEntity
from pydantic import BaseModel, ConfigDict
from structlog.stdlib import BoundLogger

from investigraph.archive import archive_source, get_archive
from investigraph.exceptions import DataError
from investigraph.model.config import Config, get_config
from investigraph.model.source import Source
from investigraph.settings import Settings
from investigraph.types import CEGenerator, RecordGenerator
from investigraph.util import make_proxy


@cache
def get_cache() -> BaseStore:
    settings = Settings()
    return settings.cache.to_store()


class DatasetContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config

    @property
    def dataset(self) -> str:
        return self.config.dataset.name

    @property
    def prefix(self) -> str:
        return self.config.dataset.prefix or self.dataset

    @property
    def cache(self) -> BaseStore:
        return get_cache()

    @property
    def store(self) -> Store:
        return get_store(self.config.load.uri)

    @property
    def log(self) -> BoundLogger:
        return get_logger(f"investigraph.datasets.{self.dataset}")

    def extract_all(self) -> RecordGenerator:
        for ctx in self.get_sources():
            yield from ctx.extract()

    def export(self, *args, **kwargs) -> DatasetStats:
        return self.config.export.handle(self, *args, **kwargs)

    def get_sources(self) -> Generator["SourceContext", None, None]:
        for source in self.config.seed.handle(self):
            yield SourceContext(config=self.config, source=source)
        for source in self.config.extract.sources:
            yield SourceContext(config=self.config, source=source)

    # RUNTIME HELPERS

    def make_proxy(self, *args, **kwargs) -> CE:
        return make_proxy(*args, dataset=self.dataset, **kwargs)

    def make(self, *args, **kwargs) -> CE:
        # align with zavod api for easy migration
        return self.make_proxy(*args, **kwargs)

    def make_slug(self, *args, **kwargs) -> str:
        prefix = kwargs.pop("prefix", self.prefix)
        slug = join_slug(*args, prefix=prefix, **kwargs)
        if not slug:
            raise ValueError("Empty slug")
        return slug

    def make_id(self, *args, **kwargs) -> str:
        prefix = kwargs.pop("prefix", self.prefix)
        id_ = join_slug(make_entity_id(*args), prefix=prefix)
        if not id_:
            raise ValueError("Empty id")
        return id_

    def make_fingerprint_id(self, *args, **kwargs) -> str:
        prefix = kwargs.pop("prefix", self.prefix)
        id_ = join_slug(make_fingerprint_id(*args), prefix=prefix)
        if not id_:
            raise ValueError("Empty id")
        return id_


class SourceContext(DatasetContext):
    source: Source

    # STAGES

    def extract(self) -> RecordGenerator:
        def _records():
            for record in self.config.extract.handle(self):
                record["__source__"] = self.source.name
                yield record

        yield from logged_items(
            _records(),
            "Extract",
            item_name="Record",
            logger=self.log,
            dataset=self.dataset,
            source=self.source.uri,
        )

    def transform(self, records: RecordGenerator) -> CEGenerator:
        def _proxies():
            for ix, record in enumerate(records, 1):
                yield from self.config.transform.handle(self, record, ix)

        yield from logged_items(
            _proxies(),
            "Transform",
            item_name="Proxy",
            logger=self.log,
            dataset=self.dataset,
            source=self.source.uri,
        )

    def load(self, proxies: CEGenerator, *args, **kwargs) -> int:
        proxies = logged_items(
            proxies,
            "Load",
            item_name="Proxy",
            logger=self.log,
            dataset=self.dataset,
            source=self.source.uri,
        )
        return self.config.load.handle(self, proxies, *args, **kwargs)

    def task(self) -> "TaskContext":
        return TaskContext(**self.model_dump())

    def open(self, **kwargs) -> ContextManager[IO[AnyStr]]:
        """
        Open the context source as a file-like handler. If `archive=True` is set
        via extract stage config, the source will be downloaded locally first.
        """
        uri = self.source.uri
        if self.config.extract.archive and not self.source.is_local:
            uri = archive_source(uri)
            archive = get_archive()
            return archive.open(uri, **kwargs)
        return smart_open(uri, **kwargs)


class TaskContext(SourceContext):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    proxies: dict[str, CompositeEntity] = {}
    data: dict[str, Any] = {}

    def __iter__(self) -> CEGenerator:
        yield from self.proxies.values()

    def emit(self, *proxies: CE | None) -> None:
        for proxy in proxies:
            if proxy is not None:
                if not proxy.id:
                    raise DataError("No Entity ID!")
                # mimic zavod api, do merge already
                if proxy.id in self.proxies:
                    self.proxies[proxy.id] = merge(self.proxies[proxy.id], proxy)
                else:
                    self.proxies[proxy.id] = proxy


@cache
def get_source_context(config_uri: Uri, source_name: str) -> SourceContext:
    config = get_config(config_uri)
    for source in config.extract.sources:
        if source.name == source_name:
            return SourceContext(config=config, source=source)
    raise ValueError(f"Source not found: `{source_name}`")


@cache
def get_dataset_context(config_uri: Uri) -> DatasetContext:
    config = get_config(config_uri)
    return DatasetContext(config=config)
