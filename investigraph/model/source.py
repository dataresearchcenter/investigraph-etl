from anystore.model import Stats
from anystore.store.resource import UriResource
from anystore.util import ensure_uri
from normality import slugify
from pydantic import BaseModel
from runpandarun import Playbook
from runpandarun.util import PathLike, absolute_path


class Source(BaseModel):
    """
    A model describing an arbitrary local or remote source.
    """

    name: str
    """Identifier of the source (defaults to slugified uri)"""

    uri: str
    """Local or remote uri of this source (via `anystore` / `fsspec`)"""

    pandas: Playbook | None = None
    """Pandas transformation spec (via `runpandarun`)"""

    data: dict | None = {}
    """Arbitrary extra data"""

    def __init__(self, **data):
        data["name"] = data.get("name", slugify(data["uri"]))
        super().__init__(**data)
        self._info: Stats | None = None

    @property
    def resource(self) -> UriResource:
        return UriResource(self.uri)

    @property
    def mimetype(self) -> str:
        return self.resource.info().mimetype

    def info(self) -> Stats:
        if self._info is None:
            self._info = self.resource.info()
        return self._info

    def ensure_uri(self, base: PathLike) -> None:
        """
        ensure absolute file paths based on base path of parent config.yml
        """
        uri = self.uri
        if self.resource.is_local:
            uri = absolute_path(uri, base)
        self.uri = ensure_uri(uri)
