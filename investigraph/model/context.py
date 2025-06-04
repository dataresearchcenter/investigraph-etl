from functools import cache, cached_property
from typing import IO, Any, AnyStr, ContextManager, Generator

from anystore import smart_open
from anystore.io import DEFAULT_MODE, Uri, get_logger, logged_items
from anystore.store import BaseStore
from followthemoney.util import make_entity_id
from ftmq.aggregate import merge
from ftmq.model import Dataset
from ftmq.store import Store, get_store
from ftmq.util import join_slug, make_fingerprint_id
from nomenklatura.entity import CE, CompositeEntity
from pydantic import BaseModel, ConfigDict
from structlog.stdlib import BoundLogger

from investigraph.archive import archive_source, get_archive
from investigraph.cache import get_archive_cache, get_runtime_cache, make_cache_key
from investigraph.exceptions import DataError
from investigraph.model.config import Config, get_config
from investigraph.model.source import Source
from investigraph.settings import Settings
from investigraph.types import CEGenerator, RecordGenerator
from investigraph.util import make_proxy


class DatasetContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config

    @property
    def dataset(self) -> str:
        """The dataset name (identifier)"""
        return self.config.dataset.name

    @property
    def prefix(self) -> str:
        """The dataset id prefix (defaults to its name)"""
        return self.config.dataset.prefix or self.dataset

    @property
    def cache(self) -> BaseStore:
        """A shared cache instance"""
        return get_runtime_cache()

    @property
    def store(self) -> Store:
        """The statement store instance to write fragments to"""
        return get_store(self.config.load.uri)

    @property
    def log(self) -> BoundLogger:
        """A structlog dataset logging instance for the runtime"""
        return get_logger(f"investigraph.datasets.{self.dataset}")

    def extract_all(self, limit: int | None = None) -> RecordGenerator:
        """
        Extract all records from all sources.

        Args:
            limit: Optionally only return this number of items per source (for
                debugging purposes)

        Yields:
            Generator of dictionaries `dict[str, Any]` that are the extracted records.
        """
        for ctx in self.get_sources():
            for ix, rec in enumerate(ctx.extract(), 1):
                if limit is not None and ix > limit:
                    break
                yield rec

    def load(self, proxies: CEGenerator, *args, **kwargs) -> int:
        """
        Load transformed records with the configured handler.
        Defaults to [`investigraph.logic.load:handle`][investigraph.logic.load]

        Args:
            proxies: Generator of `nomenklatura.entity.CompositeEntity` instances

        Returns:
            Number of entities loaded to store
        """
        proxies = logged_items(
            proxies,
            "Load",
            item_name="Proxy",
            logger=self.log,
            dataset=self.dataset,
            store=self.config.load.uri,
        )
        return self.config.load.handle(self, proxies, *args, **kwargs)

    def export(self, *args, **kwargs) -> Dataset:
        """
        Execute the configured export handler.
        Defaults to [`investigraph.logic.export:handle`][investigraph.logic.export]

        Returns:
            Dataset model instance for the pipeline dataset, with computed stats
                if configured.
        """
        return self.config.export.handle(self, *args, **kwargs)

    def get_sources(
        self, limit: int | None = None
    ) -> Generator["SourceContext", None, None]:
        """
        Get all the instances of
        [`SourceContext`][investigraph.model.context.SourceContext] for the
        current pipeline.

        Args:
            limit: Optionally only return this number of items (for debugging
                purposes)

        Yields:
            Generator for Source model instances
        """
        for ix, source in enumerate(
            (*self.config.seed.handle(self), *self.config.extract.sources), 1
        ):
            yield SourceContext(config=self.config, source=source)
            if limit is not None and limit > ix:
                return

    # RUNTIME HELPERS

    def make_proxy(self, schema: str, *args, **kwargs) -> CE:
        """
        Instantiate a new `CompositeEntity` with its schema and optional data.

        Example:
            ```python
            def transform(ctx, record, ix):
                proxy = ctx.make_proxy("Company")
                proxy.id = f"c-{ix}"
                proxy.add("name", record["name"])
            ```

        Args:
            schema: [FollowTheMoney schema](https://followthemoney.tech/explorer/)

        Returns:
            instance of `nomenklatura.entity.CompositeEntity`
        """
        return make_proxy(schema, *args, dataset=self.dataset, **kwargs)

    def make_slug(self, *args, **kwargs) -> str:
        """
        Generate a slug (usable for an entity ID). This guarantees a valid slug
        or raises an error. It either uses the configured dataset prefix or a
        custom prefix given as `prefix` keyword argument.

        Returns:
            A slug

        Raises:
            ValueError: When the slug is invalid (e.g. empty string or `None`)
        """
        prefix = kwargs.pop("prefix", self.prefix)
        slug = join_slug(*args, prefix=prefix, **kwargs)
        if not slug:
            raise ValueError("Empty slug")
        return slug

    def make_id(self, *args, **kwargs) -> str:
        """
        Generate an ID (usable for an entity ID). This guarantees a valid slug
        or raises an error. It either uses the configured dataset prefix or a
        custom prefix given as `prefix` keyword argument. The ID is generated
        from the arguments as a SHA1 hash (same as
        `followthemoney.util.make_entity_id`)

        Returns:
            An ID

        Raises:
            ValueError: When the id is invalid (e.g. empty string or `None`)
        """
        prefix = kwargs.pop("prefix", self.prefix)
        id_ = join_slug(make_entity_id(*args), prefix=prefix)
        if not id_:
            raise ValueError("Empty id")
        return id_

    def make_fingerprint_id(self, *args, **kwargs) -> str:
        """
        Generate an ID (usable for an entity ID). This guarantees a valid slug
        or raises an error. It either uses the configured dataset prefix or a
        custom prefix given as `prefix` keyword argument. The ID is generated
        from the fingerprint (using `rigour.fingerprints`) of the arguments as a
        SHA1 hash (same as `followthemoney.util.make_entity_id`)

        Returns:
            An ID based on the fingerprints of the input values

        Raises:
            ValueError: When the id is invalid (e.g. empty string or `None`)
        """
        prefix = kwargs.pop("prefix", self.prefix)
        id_ = join_slug(make_fingerprint_id(*args), prefix=prefix)
        if not id_:
            raise ValueError("Empty id")
        return id_


class SourceContext(DatasetContext):
    source: Source

    @cached_property
    def extract_key(self) -> str:
        """
        The computed cache ke for extraction for the current source.
        See [Cache][investigraph.cache]
        """
        key = make_cache_key(self.source.uri, use_checksum=True)
        if not key:
            raise ValueError(f"Empty cache key for source `{self.source.name}`")
        return f"extracted/{self.dataset}/{key}"

    @cached_property
    def should_extract(self) -> bool:
        """
        Check if the source with the same cache key was already extracted
        """
        settings = Settings()
        if settings.extract_cache:
            cache = get_archive_cache()
            if cache.exists(self.extract_key):
                self.log.info(
                    "Skipping cached source",
                    cache_key=self.extract_key,
                    source=self.source.uri,
                )
                return False
        return True

    # STAGES

    def extract(self, limit: int | None = None) -> RecordGenerator:
        """
        Extract the records for the current source with the configured handler.
        Defaults to [`investigraph.logic.extract:handle`][investigraph.logic.extract]

        Args:
            limit: Optionally only return this number of items per source (for
                debugging purposes)

        Yields:
            Generator of dictionaries `dict[str, Any]` that are the extracted records.
        """

        if not self.should_extract:
            return

        def _records():
            for ix, record in enumerate(self.config.extract.handle(self), 1):
                if limit is not None and ix > limit:
                    break
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

        cache = get_archive_cache()
        cache.touch(self.extract_key)

    def transform(self, records: RecordGenerator) -> CEGenerator:
        """
        Transform extracted records from the current source into FollowTheMoney
        entities with the configured handler.
        Defaults to [`investigraph.logic.transform:map_ftm`][investigraph.logic.transform]

        Args:
            records: Generator of record items as `dict[str, Any]`

        Yields:
            Generator of `nomenklatura.entity.CompositeEntity`
        """

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

    def task(self) -> "TaskContext":
        """
        Get a runtime task context to pass on to helper functions within
        transform stage. See [`TaskContext.emit`][investigraph.model.TaskContext.emit]

        Example:
            ```python
            def transform(ctx, record, ix):
                task_ctx = ctx.task()

                # do something, within this function use `task_ctx.emit()`
                handle_record(task_ctx, record)

                # pass on emitted entities to next stage
                yield from task_ctx
            ```

        Returns:
            The runtime task context
        """
        return TaskContext(**self.model_dump())

    def open(
        self, mode: str | None = DEFAULT_MODE, **kwargs
    ) -> ContextManager[IO[AnyStr]]:
        """
        Open the context source as a file-like handler. If `archive=True` is set
        via extract stage config, the source will be downloaded locally first.

        Example:
            ```python
            def extract(ctx, *args, **kwargs):
                with ctx.open() as h:
                    while line := h.readline():
                        yield line
            ```

        Args:
            mode: The mode to open, defaults `rb`

        Returns:
            A file-handler like context manager. The file gets closed when
                leaving the context.
        """
        uri = self.source.uri
        if self.config.extract.archive and not self.source.is_local:
            uri = archive_source(uri)
            archive = get_archive()
            return archive.open(uri, mode=mode, **kwargs)
        return smart_open(uri, mode=mode, **kwargs)


class TaskContext(SourceContext):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    proxies: dict[str, CompositeEntity] = {}
    data: dict[str, Any] = {}

    def __iter__(self) -> CEGenerator:
        yield from self.proxies.values()

    def emit(self, *proxies: CE | None) -> None:
        """
        Emit `nomenklatura.entity.CompositeEntity` instances during task
        runtime. The entities will already be merged. This is useful for helper
        functions within transform logic that create multiple entities "on the
        fly"

        Example:
            ```python
            def make_person(ctx: TaskContext, record: dict[str, Any]) -> CE:
                person = ctx.make_proxy("Person", id=1, name="Jane Doe")
                note = ctx.make_proxy("Note", id="note-1", entity=person)

                # make sure the note entity is emitted as we are only returning
                # the person entity:
                ctx.emit(note)

                return person
            ```

        """
        for proxy in proxies:
            if proxy is not None:
                if not proxy.id:
                    raise DataError("No Entity ID!")
                # do merge already
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
