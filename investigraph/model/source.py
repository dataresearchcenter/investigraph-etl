from urllib.parse import urlparse

from anystore.model import Stats
from anystore.store import get_store_for_uri
from anystore.util import SCHEME_FILE, ensure_uri
from normality import slugify
from pydantic import BaseModel
from runpandarun import Playbook
from runpandarun.util import PathLike, absolute_path

from investigraph.util import slugified_dict


class SourceInfo(Stats):
    @property
    def etag(self) -> str | None:
        raw = slugified_dict(self.raw)
        return raw.get("etag")

    @property
    def cache_key(self) -> str | None:
        if self.etag:
            return self.etag
        if self.updated_at:
            return self.updated_at.isoformat()


class Source(BaseModel):
    """
    A model describing an arbitrary local or remote source.
    """

    name: str
    """Identifier of the source (defaults to slugified uri)"""

    uri: str
    """Local or remote uri of this source (via `anystore` / `fsspec`)"""

    scheme: str
    """Uri scheme, is set automatically during initialization"""

    pandas: Playbook | None = None
    """Pandas transformation spec (via `runpandarun`)"""

    data: dict | None = {}
    """Arbitrary extra data"""

    def __init__(self, **data):
        data["uri"] = str(data["uri"])
        data["name"] = data.get("name", slugify(data["uri"]))
        data["scheme"] = data.get("scheme", urlparse(data["uri"]).scheme or "file")
        super().__init__(**data)

    def ensure_uri(self, base: PathLike) -> None:
        """
        ensure absolute file paths based on base path of parent config.yml
        """
        uri = self.uri
        if self.is_local:
            uri = absolute_path(uri, base)
        self.uri = ensure_uri(uri)

    def info(self) -> SourceInfo:
        store, uri = get_store_for_uri(self.uri)
        return SourceInfo(**store.info(uri).model_dump())

    @property
    def is_local(self) -> bool:
        return self.scheme == SCHEME_FILE

    @property
    def mimetype(self) -> str:
        return self.info().mimetype
