# Load

The transformed [entities](../concepts/entity.md) from the _transform_ stage need to be written to a _store_ that aggregates and optionally exports the entities. Under the hood, this is a _statement store_ via [ftmq](https://docs.investigraph.dev/lib/ftmq) which is based on [nomenklatura](https://github.com/opensanctions/nomenklatura).

## Fragments

One essential feature from the underlying [followthemoney toolkit](../stack/followthemoney.md) is the so called "entity fragmentation". This means, pipelines can output *partial* data for a given entity and later merge them together. For example, if one data source has information about a `Person`s birth date, and another has information about the nationality of this person, the two different pipelines would produce two different fragments of the same [entity](../concepts/entity.md) that are aggregated at a later stage. [Read more about the technical details here.](https://followthemoney.tech/docs/fragments/)

## Configure

If not configured, **investigraph** uses a simple `MemoryStore` for storing the _entity fragments_. This store only persists during runtime of the pipeline, and in that case the [_export stage_](export.md) automatically exports the entities to a local json file, even if this is not explicitly configured in the export config. If you set the store explicitly to a persistent store, the export doesn't happen automatically.

!!! warning
    To avoid memory issues with bigger datasets, set the store to another backend than `memory://`.


When using stores with _redis_, _postgresql_ or _leveldb_ backend, refer to the [install](../install.md) section for how to install investigraph with additional dependencies for these.

### Set the store uri

#### Redis or KVRocks store

Accepts any valid redis connection url.

```yaml
load:
  uri: redis://localhost
```

#### LevelDB store

Accepts any valid path to a local path in which the DB will be created if it doesn't exist.

```yaml
load:
  uri: leveldb:///data/followthemoney.ldb
```

#### SQL store

Accepts any valid sql connection string (via `sqlalchemy`).

**sqlite**

```yaml
load:
  uri: sqlite:///nomeklatura.db
```

**postgresql**

```yaml
load:
  uri: postgresql://user:password@host/database
```

### Bring your own code

Bring your own code to the loading stage.

It takes `nomenklatura.entity.CompositeEntity` proxies coming from the transform stage.

It is called for each chunk of transformed proxies.

#### config.yml

```yaml
load:
  handler: ./load.py:handle
```

#### load.py

```python
import orjson
import sys

from nomenklatura.entity import CEGenerator
from investigraph.model import DatasetContext

def handle(ctx: DatasetContext, proxies: CEGenerator):
    for proxy in proxies:
        sys.stdout.write(orjson.dumps(proxy.to_dict()))
```

#### ::: investigraph.logic.load
