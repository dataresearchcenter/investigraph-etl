# config.yml

The main entry point for a specific [dataset](../concepts/dataset.md) configuration.

!!! info "Convention"
    A dataset pipeline configuration should be named `config.yml` within a dataset folder, e.g.: `./gdho/config.yml`

Config files can be referenced via [command line](../run/cli.md):

    investigraph run -c ./path/to/config/file.yml

!!! tip
    To avoid repetitive `-c ./path/to/config.yml` flag, set the config file globally via environment variable `INVESTIGRAPH_CONFIG`.

## Content

### Dataset metadata

The dataset metadata follows the FTM dataset specification. [Full overview](https://www.opensanctions.org/docs/metadata/)

#### `name` (required)

Dataset identifier as a slug.

```yaml
name: ec_meetings
```

#### `title`

Human-readable title of the dataset.

```yaml
title: European Commission - Meetings with interest representatives
```

#### `prefix`

Slug prefix for [entity](../concepts/entity.md) IDs. If not specified, uses `name`.

```yaml
prefix: ec
```

#### `summary`

Brief description of the dataset. Can be multi-line.

```yaml
summary: |
  The Commission applies strict rules on transparency concerning its contacts
  and relations with interest representatives.
```

#### `description`

Detailed description of the dataset.

```yaml
description: |
  Full description of the dataset...
```

#### `url`

URL to the dataset homepage or source.

```yaml
url: https://example.com/dataset
```

#### `publisher`

Publisher of the dataset. Required field: `name`.

```yaml
publisher:
  name: European Commission Secretariat-General
  description: |
    The Secretariat-General is responsible for the overall coherence...
  url: https://commission.europa.eu
```

#### `maintainer`

Maintainer of the dataset (same structure as `publisher`).

```yaml
maintainer:
  name: Data Research Center
  url: https://dataresearchcenter.org
```

#### `license`

License identifier (e.g., `CC-BY-4.0`, `MIT`).

```yaml
license: CC-BY-4.0
```

#### `category`

Category of the dataset.

```yaml
category: regulatory
```

#### `tags`

List of tags for categorization.

```yaml
tags:
  - lobbying
  - transparency
```

#### `coverage`

Geographic or temporal coverage information.

```yaml
coverage:
  start: "2014-01-01"
  end: "2024-12-31"
```

#### `resources`

List of resources that hold [entities](../concepts/entity.md) from this dataset.

```yaml
resources:
  - name: entities.ftm.json
    url: https://data.ftm.store/investigraph/gdho/entities.ftm.json
    mime_type: application/json+ftm
```

#### `version`

Dataset version.

```yaml
version: "1.0.0"
```

#### `git_repo`

Git repository URL for the dataset.

```yaml
git_repo: https://github.com/org/dataset
```

#### `updated_at`

Last update timestamp (ISO 8601).

```yaml
updated_at: "2024-01-15T10:00:00Z"
```

### Seed stage

Optional stage that programmatically initializes [`Sources`][investigraph.model.Source].

```yaml
seed:
  handler: ./seed.py:handle  # custom handler (optional)
  uri: s3://bucket/prefix/   # base uri for sources
  prefix: myprefix           # only include sources with this prefix
  exclude_prefix: test       # exclude sources with this prefix
  glob: "*.csv"              # glob pattern(s) to match
  storage_options:           # fsspec storage options
    key: value
  source_options:            # extra data to pass to Source objects
    key: value
```

[See seed stage documentation](../stages/seed.md)

### Extract stage

Configuration for the extraction stage. Fetches sources and extracts records.

```yaml
extract:
  handler: ./extract.py:handle  # custom handler (optional)
  archive: true                 # download and archive remote sources (default: true)
  sources:
    - uri: https://example.com/data.csv
      name: source_name         # optional source identifier
      pandas:                   # pandas/runpandarun configuration
        read:
          handler: read_csv     # pandas read handler
          options:
            encoding: utf-8
            skiprows: 1
      data:                     # arbitrary extra data
        key: value
```

**Extract stage options:**

- `handler`: Custom extraction handler function (default: `investigraph.logic.extract:handle`)
- `archive`: Download and archive remote sources before processing (default: `true`)
- `sources`: List of source configurations
- `pandas`: Global pandas configuration applied to all sources (can be overridden per source)

**Source options:**

- `uri`: Local or remote source URI (required)
- `name`: Source identifier (defaults to slugified URI)
- `pandas`: Source-specific pandas configuration
- `data`: Arbitrary extra metadata

[See extract stage documentation](../stages/extract.md)

### Transform stage

Configuration for the transformation stage. Transforms records into [FollowTheMoney entities](../stack/followthemoney.md).

```yaml
transform:
  handler: ./transform.py:handle  # custom handler (optional)
  queries:
    - entities:
        entity_name:
          schema: Organization     # FTM schema
          keys:                    # columns to generate entity ID from
            - id_column
          key_literal: prefix      # literal prefix for entity ID
          properties:
            name:
              column: org_name     # map single column to property
            country:
              columns:             # map multiple columns to property
                - country1
                - country2
              join: ";"            # join multiple values with separator
            website:
              literal: "https://example.com"  # literal value
            aliases:
              template: "{first} {last}"      # template with column interpolation
      filters:                     # filter records
        column_name: value
      filters_not:                 # negative filters
        column_name: value
```

**Transform stage options:**

- `handler`: Custom transformation handler function (default: `investigraph.logic.transform:map_ftm`)
- `queries`: List of mapping queries (uses FTM mapping syntax)

**Query mapping options:**

- `entities`: Dictionary of entity mappings (entity name → EntityMapping)
- `filters`: Include only records matching these column values
- `filters_not`: Exclude records matching these column values

**Entity mapping options:**

- `schema`: FollowTheMoney schema name (required)
- `keys`: List of column names to generate entity ID from
- `key_literal`: Literal prefix for entity ID
- `id_column`: Use a specific column as entity ID
- `properties`: Dictionary of property mappings (property name → PropertyMapping)

**Property mapping options:**

- `column`: Map single column to property
- `columns`: Map multiple columns to property
- `join`: Separator for joining multiple column values
- `split`: Separator for splitting column value into multiple values
- `entity`: Reference to another entity in the mapping
- `format`: Format string for value transformation
- `literal`: Literal value for property
- `literals`: List of literal values for property
- `template`: Template string with `{column_name}` interpolation
- `required`: Skip entity if this property has no value (default: `false`)

[See transform stage documentation](../stages/transform.md)

### Load stage

Configuration for the load stage. Loads transformed entities into a statement store.

```yaml
load:
  handler: ./load.py:handle  # custom handler (optional)
  uri: memory://             # statement store URI
```

**Load stage options:**

- `handler`: Custom load handler function (default: `investigraph.logic.load:handle`)
- `uri`: Statement store URI (default: `memory://`)

Supported store URIs:

- `memory://` - In-memory store (default)
- `postgresql://user:pass@host/db` - PostgreSQL store
- `sqlite:///path/to/db.sqlite` - SQLite store

[See load stage documentation](../stages/load.md)

### Export stage

Configuration for the export stage. Exports dataset metadata and entities to files.

```yaml
export:
  handler: ./export.py:handle  # custom handler (optional)
  index_uri: ./data/dataset/index.json        # dataset metadata output
  entities_uri: ./data/dataset/entities.ftm.json  # entities output
```

**Export stage options:**

- `handler`: Custom export handler function (default: `investigraph.logic.export:handle`)
- `index_uri`: URI for dataset metadata export (JSON file with statistics)
- `entities_uri`: URI for entities export (FTM JSON lines format)

Both URIs support local paths and remote storage (S3, GCS, etc. via fsspec).

[See export stage documentation](../stages/export.md)

## Custom handlers

Each stage can use a custom handler function. Specify the path to a Python file and function:

```yaml
transform:
  handler: ./transform.py:handle
```

The handler file path is relative to the config file location.

**Handler signatures:**

```python
# Seed handler
def handle(ctx: DatasetContext) -> Generator[Source, None, None]:
    ...

# Extract handler
def handle(ctx: SourceContext) -> RecordGenerator:
    ...

# Transform handler
def handle(ctx: SourceContext, record: dict, ix: int) -> StatementEntities:
    ...

# Load handler
def handle(ctx: DatasetContext, proxies: StatementEntities) -> int:
    ...

# Export handler
def handle(ctx: DatasetContext) -> Dataset:
    ...
```

## A complete example

Taken from the [tutorial](../tutorial.md):

```yaml
name: gdho
title: Global Database of Humanitarian Organisations
prefix: gdho
summary: |
  GDHO is a global compendium of organisations that provide aid in humanitarian
  crises. The database includes basic organisational and operational
  information on these humanitarian providers, which include international
  non-governmental organisations (grouped by federation), national NGOs that
  deliver aid within their own borders, UN humanitarian agencies, and the
  International Red Cross and Red Crescent Movement.
resources:
  - name: entities.ftm.json
    url: https://data.ftm.store/investigraph/gdho/entities.ftm.json
    mime_type: application/json+ftm
publisher:
  name: Humanitarian Outcomes
  description: |
    Humanitarian Outcomes is a team of specialist consultants providing
    research and policy advice for humanitarian aid agencies and donor
    governments.
  url: https://www.humanitarianoutcomes.org

extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
      pandas:
        read:
          options:
            encoding: latin
            skiprows: 1

transform:
  queries:
    - entities:
        org:
          schema: Organization
          key_literal: gdho
          keys:
            - Id
          properties:
            name:
              column: Name
            weakAlias:
              column: Abbreviated name
            legalForm:
              column: Type
            website:
              column: Website
            country:
              column: HQ location
            incorporationDate:
              column: Year founded
            dissolutionDate:
              column: Year closed
            sector:
              columns:
                - Sector
                - Religious or secular
                - Religion

export:
  index_uri: s3://data.ftm.store/investigraph/gdho/index.json
  entities_uri: s3://data.ftm.store/investigraph/gdho/entities.ftm.json
```
