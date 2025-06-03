# Extract

In the first step of a pipeline, we focus on getting one or more data sources and extracting data records from them that will eventually be passed to the _transform stage_.

This stage is configured via the `extract` key within the `config.yml`

## config.yml

### `extract.sources`

[See sources config below](#source)

### `extract.handler`

Reference to the python function that handles this stage.

Default: `investigraph.logic.extract:handle`

When using your own extractor, you can disable source fetching by investigraph, instead fetch (and extract) your sources within your own code:

```yaml
extract:
  handler: ./extract.py:handle
```

[Bring your own code (below)](#bring-your-own-code)

### `extract.pandas`

Pandas operations to apply to the data (see [runpandarun](https://github.com/simonwoerpel/runpandarun)), including [datapatch](https://github.com/pudo/datapatch)

```yaml
extract:
  pandas:
    read:
      options:
        skiprows: 2
    operations:
      - handler: DataFrame.fillna
        options:
          value: ""
    patch:
      countries:
        - match: "Greet Britain"
          value: "Great Britain"
```

Can also be applied per source:

```yaml
extract:
  sources:
    - uri: test.csv
      options:
        pandas:
          # ...
```


## Source

A data source is defined by a `uri`. As investigraph is using [fsspec](https://github.com/fsspec/filesystem_spec) under the hood, this `uri` can be anything from a local file path to a remote s3 resource.

Examples for source uris:
```
s3://my_bucket/data.csv
gs://my_bucket/data.csv
azure://my_bucket/data.csv
hdfs:///path/data.csv
hdfs://path/data.csv
webhdfs://host:port/path/data.csv
./local/path/data.csv
~/local/path/data.csv
local/path/data.csv
./local/path/data.csv.gz
file:///home/user/file.csv
file:///home/user/file.csv.bz2
[ssh|scp|sftp]://username@host//path/file.csv
[ssh|scp|sftp]://username@host/path/file.csv
[ssh|scp|sftp]://username:password@host/path/file.csv
```

And, of course, just `http[s]://...`

A pipeline can have more than one source and is defined in the [`config.yml`](../reference/config.md) within the `extract.sources[]` key. This can either be just a list of one or more `uri`s or of more complex source objects.

### Simple source

```yaml
extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
```

This tells the pipeline to fetch the output from the given url without any more logic.

As seen in the [tutorial](../tutorial.md), this source has actually encoding problems and we want to skip the first line. So we need to give investigraph a bit more information on how to extract this source (see tutorial and options below).

### Named source

You can give a name (or identifier) to the source to be able to identify in your code from which source the generated records are coming from, e.g. to adjust a parsing function based on the source file.

```yaml
extract:
  sources:
    - name: ec_juncker
      uri: https://ec.europa.eu/transparencyinitiative/meetings/dataxlsx.do?name=meetingscommissionrepresentatives1419
    - name: ec_leyen
      uri: https://ec.europa.eu/transparencyinitiative/meetings/dataxlsx.do?name=meetingscommissionrepresentatives1924
```

This helps us for the [transform stage](./transform.md) to distinguish between different sources and adjust our parsing code to it.

### More configurable source

For extracting most kinds of sources, investigrap uses [runpandarun](../stack/runpandarun.md) under the hood. This is a wrapper around [pandas](https://pandas.pydata.org) that allows specifying a pandas workflow as a yaml playbook. Pandas has a lot of options on how to read in data, and within our `config.yml` we can just pass any arbitrary argument to [`pandas.read_csv`](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html#pandas.read_csv) or [`pandas.read_excel`](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_excel.html#pandas-read-excel). (`runpandarun` is picking the right function based on the sources mimetype.)

Just put the required arguments in the config key `extract.sources[].pandas`, in this case (see tutorial) like this:

```yaml
extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
      pandas:
        read:
          options:
            encoding: latin
            skiprows: 1

```

Under the hood, this calls
```python
pandas.read_csv(uri, encoding="latin", skiprows=1)
```

If `runpandarun` is not able to detect the handler to read in the source, as happening in misconfigured web headers or wrong file extensions, you can manually specify the `read.handler`:

```yaml
extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
      pandas:
        read:
          handler: read_csv
          options:
            encoding: latin
            skiprows: 1
```

### Prepare your data with pandas

In case you want to use the built-in support for [followthemoney mappings](https://followthemoney.tech/docs/mappings/#mappings), you might need to adjust the incoming data a bit more, as per design, `followthemoney` expects an already quite cleaned tabular source.

With the help of [runpandarun](../stack/runpandarun.md) we can basically do anything we need with the source data:

```yaml
extract:
  sources:
    - uri: ./data.csv
      pandas:
        read:
          options:
            skiprows: 3
        operations:
          - handler: DataFrame.rename
            options:
              columns:
                value: amount
                "First name": first_name
          - handler: DataFrame.fillna
            options:
              value: ""
          - handler: Series.map
            column: slug
            options:
              func: "lambda x: normality.slugify(x) if isinstance(x) else 'NO DATA'"
```

This "pandas playbook" translates into these python calls that **investigraph** will run:

```python
import pandas as pd
import normality

df = pd.read_csv("./data.csv", skiprows=3)
df = df.rename(columns={"value": "amount", "First name": "first_name"})
df = df.fillna("")
df["slug"] = df["slug"].map(lambda x: normality.slugify(x) if isinstance(x) else 'NO DATA')
```

Refer to the [runpandarun documentation](https://github.com/simonwoerpel/runpandarun) for more.

To apply the same pandas transformations to _all_ sources, use the `sources.pandas` key instead:

```yaml
extract:
  sources:
    - uri: ./data1.csv
    - uri: ./data2.csv
  pandas:
    read:
      options:
        skiprows: 3
```


### Apply data patches

[runpandarun](https://github.com/simonwoerpel/runpandarun) ships with [datapatch](https://github.com/pudo/datapatch) integrated, so you can apply data patches *after* the pandas operations are applied:

```yaml
extract:
  sources:
    - uri: ./data.csv
      pandas:
        read:
          options:
            skiprows: 3
        operations:
          - handler: DataFrame.fillna
            options:
              value: ""
        patch:
          countries:
            - match: "Greet Britain"
              value: "Great Britain"
```

## Inspecting records

To iteratively test your configuration, you can use `investigraph extract` to see what output the extract stage is producing:

    investigraph extract -c path/to/config.yml

Limit to only get the 10 first records:

    investigraph extract -c path/to/config.yml -l 10

To output the first records as `csv`:

    investigraph extract -c path/to/config.yml -l 10 --output-format csv

## Archiving remote sources

Per default, **investigraph** stores remote sources in a local archive. To disable this behaviour, set `extract.archive` to `false`:

```yaml
extract:
  archive: false
  sources:
    - # ...
```

## Bring your own code

Bring your own code to the extraction stage.

The entrypoint function must yield dictionaries that will be passed as records to the next stage to transform.

### config.yml

!!! info "Convention"
    Custom handlers should be one python file per stage (`extract.py`) in the dataset folder (next to `config.yml`) that contain a main `handle` function.


```yaml
extract:
  sources:
    - uri: https://example.com/data.csv
  handler: ./extract.py:handle
```

### extract.py

```python
import csv
from io import StringIO
from typing import Any, Generator

from investigraph.model import SourceContext

def handle(ctx: SourceContext, *args, **kwargs) -> Generator[dict[str, Any], None, None]:
    # download and open the source:
    with ctx.open("r") as fh:
      yield from csv.DictReader(fh)
```

### Reference

#### ::: investigraph.logic.extract
