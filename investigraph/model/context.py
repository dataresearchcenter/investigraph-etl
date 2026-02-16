from datetime import datetime
from functools import cache, cached_property
from typing import IO, Any, AnyStr, ContextManager, Generator

from anystore import smart_open
from anystore.interface.tags import Tags, get_tags
from anystore.io import logged_items
from anystore.logging import get_logger
from anystore.logic.constants import DEFAULT_MODE
from anystore.store import Store as AnyStore
from anystore.types import Uri
from anystore.util import join_relpaths
from followthemoney import StatementEntity
from followthemoney.util import make_entity_id
from ftm_lakehouse import get_lakehouse
from ftm_lakehouse.core.settings import Settings as LakeSettings
from ftm_lakehouse.dataset import Dataset as LakeDataset
from ftm_lakehouse.dataset import EntityRepository
from ftm_lakehouse.repository.factories import get_tags as get_lake_tags
from ftm_lakehouse.storage.tags import TagStore
from ftmq.aggregate import merge
from ftmq.model import Dataset
from ftmq.store import Store as FtmStore
from ftmq.store import get_store as get_ftm_store
from ftmq.types import StatementEntities
from ftmq.util import join_slug, make_fingerprint_id
from memorious.logic.fetch import fetch
from pydantic import BaseModel, ConfigDict
from structlog.stdlib import BoundLogger

from investigraph.exceptions import DataError
from investigraph.model.config import Config, get_config
from investigraph.model.source import Source
from investigraph.settings import Settings
from investigraph.types import RecordGenerator
from investigraph.util import make_entity

settings = Settings()
lake_settings = LakeSettings()


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

    @cached_property
    def cache(self) -> AnyStore:
        """A shared cache instance"""
        return settings.cache.to_store()

    @cached_property
    def store(self) -> FtmStore | EntityRepository:
        """The statement store instance to write fragments to"""
        if self.lake:
            return self.lake.entities
        return get_ftm_store(self.config.load.uri, dataset=self.config.dataset.name)

    @cached_property
    def tags(self) -> Tags | TagStore:
        if settings.tags_uri:
            return get_tags(settings.tags_uri)
        if self.lake:
            return get_lake_tags(self.dataset, tenant="investigraph")
        return get_tags("memory://")

    def make_tag_key(self, *parts) -> str | None:
        for part in parts:
            if not part:
                return
        return join_relpaths(self.dataset, *parts)

    @cached_property
    def lake(self) -> LakeDataset | None:
        if settings.is_lakehouse:
            lake = get_lakehouse()
            return lake.get_dataset(self.dataset)

    @property
    def log(self) -> BoundLogger:
        """A structlog dataset logging instance for the runtime"""
        return get_logger(f"investigraph.datasets.{self.dataset}", dataset=self.dataset)

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

    def load(self, proxies: StatementEntities, *args, **kwargs) -> int:
        """
        Load transformed records with the configured handler.
        Defaults to [`investigraph.logic.load:handle`][investigraph.logic.load]

        Args:
            proxies: Generator of StatementEntity instances

        Returns:
            Number of entities loaded to store
        """
        if self.lake:
            store_uri = self.lake.uri
        else:
            store_uri = self.config.load.uri
        proxies = logged_items(
            proxies,
            "Load",
            item_name="Proxy",
            logger=self.log,
            store=store_uri,
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

        def _sources():
            yield from self.config.seed.handle(self)
            yield from self.config.extract.sources

        for ix, source in enumerate(_sources(), 1):
            yield SourceContext(config=self.config, source=source)
            if limit is not None and ix >= limit:
                return

    # RUNTIME HELPERS

    def make_entity(self, schema: str, *args, **kwargs) -> StatementEntity:
        """
        Instantiate a new Entity with its schema and optional data.

        Example:
            ```python
            def transform(ctx, record, ix):
                proxy = ctx.make_entity("Company")
                proxy.id = f"c-{ix}"
                proxy.add("name", record["name"])
            ```

        Args:
            schema: [FollowTheMoney schema](https://followthemoney.tech/explorer/)

        Returns:
            instance of StatementEntity
        """
        return make_entity(schema, *args, dataset=self.dataset, **kwargs)

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

    # STAGES

    def extract(self, limit: int | None = None) -> RecordGenerator:
        """
        Extract the records for the current source with the configured handler.
        Defaults to [`investigraph.logic.extract:handle`][investigraph.logic.extract]

        Extraction is skipped if INVESTIGRAPH_INCREMENTAL=true and a cache key
        for this source already exists.

        Args:
            limit: Optionally only return this number of items per source (for
                debugging purposes)

        Yields:
            Generator of dictionaries `dict[str, Any]` that are the extracted records.
        """
        cache_key = self.make_tag_key("extract", self.source.cache_key)
        if settings.incremental and cache_key and self.tags.exists(cache_key):
            self.log.info(
                f"Skipping source `{self.source.uri}`, cached",
                source=self.source.uri,
                cache_key=cache_key,
            )
            return

        def _records():
            for ix, record in enumerate(self.config.extract.handle(self), 1):
                if limit is not None and ix > limit:
                    return
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

        if cache_key:
            self.tags.put(cache_key, datetime.now())

    def transform(self, records: RecordGenerator) -> StatementEntities:
        """
        Transform extracted records from the current source into FollowTheMoney
        entities with the configured handler.
        Defaults to [`investigraph.logic.transform:map_ftm`][investigraph.logic.transform]

        Args:
            records: Generator of record items as `dict[str, Any]`

        Yields:
            Generator of StatementEntity
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
        Open the context source as a file-like handler. Use cache from archive
        if feasible.

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
        if self.source.resource.is_http:
            response = fetch(uri, dataset=self.dataset)
            return response.context.open(response.content_hash)
        return smart_open(uri, mode=mode, **kwargs)


class TaskContext(SourceContext):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    proxies: dict[str, StatementEntity] = {}
    data: dict[str, Any] = {}

    def __iter__(self) -> StatementEntities:
        yield from self.proxies.values()

    def emit(self, *proxies: StatementEntity | None) -> None:
        """
        Emit Entity instances during task
        runtime. The entities will already be merged. This is useful for helper
        functions within transform logic that create multiple entities "on the
        fly"

        Example:
            ```python
            def make_person(ctx: TaskContext, record: dict[str, Any]) -> E:
                person = ctx.make_entity("Person", id=1, name="Jane Doe")
                note = ctx.make_entity("Note", id="note-1", entity=person)

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
def get_source_context(
    config_uri: Uri, source_name: str, uri: str | None = None
) -> SourceContext:
    config = get_config(config_uri)
    for source in config.extract.sources:
        if source.name == source_name:
            return SourceContext(config=config, source=source)
    if len(config.extract.sources) == 1:
        return SourceContext(config=config, source=config.extract.sources[0])
    if uri:
        return SourceContext(config=config, source=Source(name=source_name, uri=uri))
    raise ValueError(f"Source not found: `{source_name}`")


@cache
def get_dataset_context(config_uri: Uri) -> DatasetContext:
    config = get_config(config_uri)
    return DatasetContext(config=config)
