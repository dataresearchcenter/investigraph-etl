from functools import cache
from os import PathLike
from pathlib import Path
from typing import Self
from urllib.parse import urlparse

from anystore.model.base import BaseModel
from anystore.types import Uri
from anystore.util import ensure_uri
from ftmq.model import Dataset
from pydantic import ConfigDict
from runpandarun.util import absolute_path

from investigraph.model.stage import (
    ExportStage,
    ExtractStage,
    LoadStage,
    SeedStage,
    TransformStage,
)
from investigraph.settings import Settings
from investigraph.util import is_module

settings = Settings()


class Config(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataset: Dataset
    base_path: Path = Path()
    seed: SeedStage = SeedStage()
    extract: ExtractStage = ExtractStage()
    transform: TransformStage = TransformStage()
    load: LoadStage = LoadStage()
    export: ExportStage = ExportStage()

    def __init__(self, **data):
        if "dataset" not in data:
            data["dataset"] = data
        super().__init__(**data)
        # ensure absolute file paths for local sources
        self.base_path = Path(self.base_path).absolute()
        for source in self.extract.sources:
            source.ensure_uri(self.base_path)

    @classmethod
    def from_uri(cls, uri: Uri, base_path: PathLike | None = None) -> Self:
        if base_path is None:
            u = urlparse(str(uri))
            if not u.scheme or u.scheme == "file":
                base_path = Path(uri).absolute().parent
        config = cls._from_uri(uri, base_path=base_path)

        # custom user code
        if not is_module(config.seed.handler):
            config.seed.handler = str(
                absolute_path(config.seed.handler, config.base_path)
            )
        if not is_module(config.extract.handler):
            config.extract.handler = str(
                absolute_path(config.extract.handler, config.base_path)
            )
        if not is_module(config.transform.handler):
            config.transform.handler = str(
                absolute_path(config.transform.handler, config.base_path)
            )
        if not is_module(config.load.handler):
            config.load.handler = str(
                absolute_path(config.load.handler, config.base_path)
            )
        if not is_module(config.export.handler):
            config.export.handler = str(
                absolute_path(config.export.handler, config.base_path)
            )

        # ensure base export uris when using memory store
        if config.load.uri.startswith("memory"):
            if config.export.entities_uri is None:
                config.export.entities_uri = ensure_uri(
                    settings.data_root / config.dataset.name / "entities.ftm.json"
                )
            if config.export.index_uri is None:
                config.export.index_uri = ensure_uri(
                    settings.data_root / config.dataset.name / "index.json"
                )

        return config


@cache
def get_config(
    uri: Uri, index_uri: Uri | None = None, entities_uri: Uri | None = None
) -> Config:
    config = Config.from_uri(uri)
    config.export.index_uri = index_uri or config.export.index_uri
    config.export.entities_uri = entities_uri or config.export.entities_uri
    return config
