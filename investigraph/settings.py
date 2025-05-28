import os
from pathlib import Path

from anystore.model import StoreModel
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

VERSION = "0.6.1"

DATA_ROOT = Path(
    os.environ.get("INVESTIGRAPH_DATA_ROOT", Path.cwd() / "data")
).absolute()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="investigraph_",
        env_nested_delimiter="_",
        nested_model_default_partial_update=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = Field(default=False, alias="debug")

    data_root: Path = DATA_ROOT

    seeder: str = "investigraph.logic.seed:handle"
    extractor: str = "investigraph.logic.extract:handle"
    transformer: str = "investigraph.logic.transform:map_ftm"
    loader: str = "investigraph.logic.load:handle"
    exporter: str = "investigraph.logic.export:handle"

    archive: StoreModel = StoreModel(uri=DATA_ROOT / "archive")
    cache: StoreModel = StoreModel(uri="memory:///")
    store_uri: str = Field(default="memory:///", alias="ftmq_store_uri")
