# config.yml

The main entry point for a specific [dataset](../concepts/dataset.md) configuration.

!!! info "Convention"
    A dataset pipeline configuration should be named `config.yml` within a dataset folder, e.g.: `./gdho/config.yml`

Config files can be referenced to use via [command line](../run/cli.md):

    investigraph run -c ./path/to/config/file.yml

!!! tip
    To avoid repetitive `-c ./path/to/config.yml` flag, set the config file globally via environment variable `INVESTIGRAPH_CONFIG`.

## Content

### Dataset metadata

[A full overview for all dataset metadata properties](https://www.opensanctions.org/docs/metadata/)

#### `name`

**required**

Dataset identifier, as a slug

Example: `ec_meetings`

#### `title`

Human-readable title of the dataset

Example: `European Commission - Meetings with interest representatives`

Default: capitalized `name` from above.

#### `prefix`

slug prefix for [entity](../concepts/entity.md) IDs.

Example: `ec`

Default: `None`

#### `country`

2-letter iso code of the main country this dataset is related to. Also accepts `eu`.

Example: `eu`

Default: `None`

#### `summary`

A description about the dataset, can be multi-lined.

Example:

```yaml
description: |
    The Commission applies strict rules on transparency concerning its contacts
    and relations with interest representatives. # ...
```

Default: `None`

#### `resources`

A list of resources that hold [entities](../concepts/entity.md) from this dataset.

Example:

```yaml
resources:
  - name: entities.ftm.json
    url: https://data.ftm.store/investigraph/ec_meetings/entities.ftm.json
    mime_type: application/json+ftm
  - # ...
```

Default: `None`

#### `publisher`

Publisher of the dataset as an object. Required key: `name`

Example:

```yaml
publisher:
  name: European Commission Secretariat-General
  description: |
    The Secretariat-General is responsible for the overall coherence of the
    Commission’s work – both in shaping new policies, and in steering them
    through the other EU institutions. It supports the whole Commission.
  url: https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/secretariat-general_en
```

Default: `None`

### Seed stage

Optional stage prior to extract that programmatically initializes [`Sources`][investigraph.model.Source].

```yaml
seed:
  uri:  # base uri
  # ...
```

[See seed stage](../stages/seed.md)

### Extract stage

Configuration for the extraction stage, for fetching sources and extracting records to transform in the next stage.

```yaml
extract:
  sources:
    - # ...
```

[See extract stage](../stages/extract.md)

### Transform stage

Configuration for the transformation stage, for defining a [FollowTheMoney mapping](../stack/followthemoney.md) or referencing custom transformation code. When a custom handler is defined, the query mapping is ignored.

```yaml
transform:
  queries:
    - entities:
    # FtM mappings
```

[See transform stage](../stages/transform.md)

### Load stage

This stage loads the transformed [Entities](../concepts/entity.md) into defined targets.

```yaml
load:
  uri: # statement store uri
```

[See load stage](../stages/load.md)

### Export stage

This optional stage exports datased index (including statistics) and _Entities_ to json files at local or remote targets.

```yaml
export:
  index_uri:  # uri for dataset metadata index.json
  entities_uri:  # uri for entities.ftm.json
```

[See export stage](../stages/export.md)

## A complete example

Taken from the [tutorial](../tutorial.md)

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
