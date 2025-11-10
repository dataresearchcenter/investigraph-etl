# Transform

As outlined, **investigraph** tries to automate everything *around* this stage. That's because transforming any arbitrary source data into [ftm entities](../concepts/entity.md) is very dependent on the actual dataset.

Still, for simple use cases, you don't need to write any `python code` here at all. Just define a *mapping*. For more complex scenarios, write your own `transform` function.

## Mapping

Simply plug in a standardized ftm mapping (as [described here](https://followthemoney.tech/docs/mappings/#mappings)) into your pipeline configuration under the root key `transform.queries`:

```yaml
transform:
  queries:
    - entities:
        org:
          schema: Organization
          keys:
            - Id
          properties:
            name:
              column: Name
            # ...
```

As it follows the mapping specification from [Follow The Money](../stack/followthemoney.md), any existing mapping can be copied over here and a mapping can easily (and independent of investigraph) tested with the ftm command line:

    ftm map-csv ./<dataset>/config.yml -i ./data.csv

Please refer to the [aleph documentation](https://docs.aleph.occrp.org/developers/mappings/) for more details about mappings.

## Bring your own code

For more complex transforming operations, just write your own code. As described, one of the main values of **investigraph** is that you only have to write this one python file for a dataset, everything else is handled automatically.

!!! info "Convention"
    In the `<stage>.handler` key, you can either refer to a python function via it's module path, or to a file path to a python script containing the function. In that case, by convention the python files should be named after their stages (`seed.py`, `extract.py`, `transform.py`, `load.py`, `export.py`) and live in the same directory as the datasets `config.yml`. The main entrypoint function should be called `handle()`.

### Refer a function from a module

The module must be within the current `PYTHONPATH` at runtime.

```yaml
transform:
    handler: my_library.transformers:wrangle
```

### Refer a function from a local python script file

```yaml
transform:
    handler: ./transform.py:handle
```

The entrypoint function for the **transform stage** has the following signature:

```python
def handle(ctx: investigraph.model.SourceContext, data: dict[str, typing.Any], ix: int) -> typing.Generator[nomenklatura.entity.CE, None, None]:
    # transform `data` into one or more entities ...
    yield proxy
```

Ok. Let's break this down.

`ctx` contains the actual flow run context with some helpful information like:

- `ctx.dataset` the current dataset name
- `ctx.source` the current [source][investigraph.model.source] from which the current data record comes from

`data` is the current extracted record.

`ix` is an integer of the index of the current record.

An actual `transform.py` for the `gdho` dataset could look like this:

```python
from ftmq.types import CEGenerator
from investigraph.types import Record
from investigraph.model import SourceContext

def parse(ctx: SourceContext, record: Record, ix: int):
    proxy = ctx.make_entity("Organization", record.pop("Id"))  # schema, id
    proxy.add("name", record.pop("Name"))
    # add more property data ...
    yield proxy
```

The util function [`make_entity`][investigraph.model.DatasetContext.make_entity] creates an [entity](../concepts/entity.md), which is implemented in `nomenklatura.entity.CompositeEntity`, with the schema "Organization".

Then, following the [ftm python api](https://followthemoney.tech/docs/api/), properties can be added via `proxy.add(<prop>, <value>)`

### Transformation depending on source

The [`SourceContext`][investigraph.model.SourceContext] object contains information about the current extracted [`Source`][investigraph.model.source], so transformation logic can depend on that:

```python
def parse(ctx: SourceContext, record: Record, ix: int):
    if ctx.source.name == "persons":
        yield from handle_person_record(ctx, record)
    else:
        yield from handle_org_record(ctx, record)
```

### Reference

#### ::: investigraph.logic.transform


## Inspecting transform stage

To iteratively test your configuration, you can use `investigraph transform` to see what output the transform stage is producing from incoming records.

We make use of bash piping here to feed in the first 10 records of the previous _extract_ stage:

    investigraph extract -c path/to/config.yml -l 10 | investigraph transform -c path/to/config.yml

This will output the first few mappend [entities](../concepts/entity.md).
