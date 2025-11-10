# Tutorial

**investigraph** is a framework for extracting data from sources and transforming it into the [FollowTheMoney](https://followthemoney.tech) format. This format is used for representing entities (people, companies, organizations) and their relationships.

This tutorial shows you how to build a simple dataset without writing Python code - just YAML configuration. You'll need Python 3.11 or higher.

## 1. Installation

!!! tip
    It is highly recommended to use a [python virtual environment](https://learnpython.com/blog/how-to-use-virtualenv-python/) for installation.


```bash
pip install investigraph
```

After completion, verify that **investigraph** is installed:

```bash
investigraph --help
```

## 2. Create a dataset

We'll use [The Global Database of Humanitarian Organisations](https://www.humanitarianoutcomes.org/gdho/search) as an example - a list of humanitarian organizations worldwide.

### Setup

Every dataset needs a unique identifier (`name`). We'll use `gdho` for this dataset.

Create a directory and config file:

```bash
mkdir -p datasets/gdho
```

Create `datasets/gdho/config.yml` with basic metadata:

```yaml
name: gdho
title: Global Database of Humanitarian Organisations
publisher:
  name: Humanitarian Outcomes
  url: https://www.humanitarianoutcomes.org
```

### Add a data source

Next, specify where to fetch the data from:

```yaml
# metadata ...
extract:
  sources:
    - uri: <url>
```

The GDHO website has a "DOWNLOAD CSV" link that provides the data: [https://www.humanitarianoutcomes.org/gdho/search/results?format=csv](https://www.humanitarianoutcomes.org/gdho/search/results?format=csv)

Add this URL to the config:

```yaml
# metadata ...
extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
```

Test the extraction with:

```bash
investigraph extract -c ./datasets/gdho/config.yml -l 10
```

This will likely fail with a `utf-8` encoding error. The CSV file uses `latin` encoding and has an empty row at the top. Fix this by adding pandas options (investigraph uses [pandas.read_csv](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) internally):


```yaml
# metadata ...
extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
      pandas:
        read:
          options:
            encoding: latin
            skiprows: 1
```

Now extraction should work:

```bash
investigraph extract -c ./datasets/gdho/config.yml -l 10
```

### Transform to FollowTheMoney entities

The core step is transforming CSV data into [FollowTheMoney](https://followthemoney.tech) entities. Define a mapping from CSV columns to entity properties.

For GDHO, we'll create [Organization](https://followthemoney.tech/explorer/schemata/Organization/) entities:

```yaml
# metadata ...
# extract ...
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
```

Test the transformation:

```bash
investigraph extract -c datasets/gdho/config.yml -l 10 | investigraph transform -c datasets/gdho/config.yml
```

This outputs FollowTheMoney entities in JSON format. Add more fields by mapping additional CSV columns:

```yaml
# metadata ...
# extract ...
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
            website:
              column: Website
```

### Complete configuration

Here's the full config with all fields mapped:

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
```

## 3. Run the pipeline

Execute the full pipeline (extract, transform, load):

```bash
investigraph run -c datasets/gdho/config.yml
```

This creates a `data/gdho/` directory with the output files containing FollowTheMoney entities.

## Advanced: Custom Python code

For complex transformations beyond YAML mappings, write custom Python code. Create `datasets/gdho/transform.py`:

```python
def handle(ctx, record, ix):
    proxy = ctx.make_entity("Organization")
    proxy.id = record.pop("Id")
    proxy.add("name", record.pop("Name"))
    # add more property data ...
    yield proxy
```

Update `config.yml` to use the Python handler:

```yaml
# metadata ...
# extract ...
transform:
  handler: ./transform.py:handle
```

Run the pipeline:

```bash
investigraph run -c ./datasets/gdho/config.yml
```

## Next Steps

You can extract most data sources using only YAML configuration. For complex transformations, use custom Python code. See the [full documentation](./build/index.md) for more details.
