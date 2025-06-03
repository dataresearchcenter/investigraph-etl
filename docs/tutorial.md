# Tutorial

**investigraph** tries to automate as many functionality for different stages (extract, transform, load) as possible with no coding required.

The only thing you have to manage by yourself is the **dataset configuration**, which, in the easiest scenario, is just a `YAML` file that contains a bit of metadata and pipeline instructions.

The following tutorial is a simple setup on your local machine and only requires recent python >= 3.11.

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

## 2. Create a dataset definition

Let's start with a simple, public available dataset: [The Global Database of Humanitarian Organisations](https://www.humanitarianoutcomes.org/gdho/search). It's just a list of, yes, humanitarian organisations.

### Metadata

Every dataset needs a unique identifier, called `name` (or `foreign_id` in [OpenAleph](https://openaleph.org)). By convention, we use this identifier as well in the directory structure as a sub-folder. Let's use `gdho` here. We will reference this dataset always with this identifier.

Create a subfolder:

    mkdir -p datasets/gdho

Create the configuration file with the editor of your choice. The path to the file (by convention) should be:

    datasets/gdho/config.yml

Enter the identifier and a bit of metadata into the file:

```yaml
name: gdho
title: Global Database of Humanitarian Organisations
publisher:
  name: Humanitarian Outcomes
  url: https://www.humanitarianoutcomes.org
```

That's enough metadata for now, there is a lot more metadata possible which is covered in the documentation.

### Sources

The most interesting part of course is the pipeline definition! We have at least to provide a source:

```yaml
# metadata ...
extract:
  sources:
    - uri: <url>
```

We need to find out the remote url we want to fetch. So, open the [landing page](https://www.humanitarianoutcomes.org/gdho/search) from the GDHO dataset.

When clicking on "VIEW ALL DATA", it will open [this page](https://www.humanitarianoutcomes.org/gdho/search). And, great! There is a direct link to "DOWNLOAD CSV" which actually returns data in csv format: [https://www.humanitarianoutcomes.org/gdho/search/results?format=csv](https://www.humanitarianoutcomes.org/gdho/search/results?format=csv)

We can just add this url to our source configuration:

```yaml
# metadata ...
extract:
  sources:
    - uri: https://www.humanitarianoutcomes.org/gdho/search/results?format=csv
```

**investigraph** allows to interactively inspect your building blocks or stages for datasets, so let's try if the configuration file contains any errors:

    investigraph inspect -c ./datasets/gdho/config.yml

This will show an error about no parsing function defined, but we will fix that later.

We can inspect the outcome of the _extract_ stage for our remote source as well (the `-l` option sets a limit to show only 10 records):

    investigraph extract -c ./datasets/gdho/config.yml -l 10

Ooops! This shows us a python exception saying something about `utf-8` error. Yeah, we still have that in 2023.

When downloading this csv file manually and opening in a spreadsheet application, you will actually notice that it is in `latin` encoding and has 1 empty row at the top. 🤦 (welcome to real world data)

Under the hood, **investigraph** is using [pandas.read_csv](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html#pandas.read_csv) and there is an option `pandas` to pass instructions to pandas on how to read this csv. In this case, it would look like this (refer to the `pandas` documentation for all options):


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

Now **investigraph** is able to fetch and parse the csv source:

    investigraph extract -c ./datasets/gdho/config.yml -l 10

### Transform data

This is the core functionality of this whole thing: Transform extracted source data into the [followthemoney](https://followthemoney.tech) model.

The easiest way is to define a mapping of csv columns to ftm properties, [as described in the FollowTheMoney documentation](https://followthemoney.tech/docs/mappings/).

The format in **investigraph**s `config.yml` aligns with the ftm mapping spec, so you could use any existing mapping here as well.

For the `gdho` dataset, we want to create [Organization](https://followthemoney.tech/explorer/schemata/Organization/) entities and map the name column to the name property.

Add this mapping spec to the `config.yml` (the csv column with the name is called `Name`, so this is a no-brainer):

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

You can inspect the transformation like this:

    investigraph extract -c datasets/gdho/config.yml -l 10 | investigraph transform -c datasets/gdho/config.yml

Yay – it is returning some [FtM entities](./concepts/entity.md) 🎉

In the source data is a lot more metadata about the organizations. Refer to the [FtM mapping documentation](https://followthemoney.tech/docs/mappings/) on how to map data. Let's add the organizations website to the `properties` key:

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

Inspect again, and the entities now have the `website` property.

### The complete config.yml

Adding in a bit more metadata and property mappings:

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

To actually run the pipeline within the **investigraph framework**, execute a complete run:

    investigraph run -c datasets/gdho/config.yml

Voilà, you just transformed the whole gdho database into FtM entities! You may notice, that this execution created a new subfolder in the current working directory named `data/gdho` where you find the data output of this process.

## Optional: use python code to transform data

Instead of writing the FtM mapping in the `config.yml`, which can be a bit limiting for advanced use cases, you can instead write arbitrary python code. The code needs to live anywhere relatively to the `config.yml`, e.g. next to it in a file `transform.py`. In it, write your own _transform_ (or _extract_, or _load_) function.

To transform the records within python and achieve the same result for the `gdho` dataset, an example script would look like this:

```python
def handle(ctx, record, ix):
    proxy = ctx.make_proxy("Organization")
    proxy.id = record.pop("Id")
    proxy.add("name", record.pop("Name"))
    # add more property data ...
    yield proxy
```

Now, tell the `transform` key in the `config.yml` to use this python file instead of the defined mapping:

```yaml
# metadata ...
# extract ...
transform:
  queries: # ...
  handler: ./transform.py:handle
```

After it, run the pipeline:

    investigraph run -c ./datasets/gdho/config.yml

## Conclusion

We have shown how we can extract a datasource without the need to write any python code, just with yaml specifications. [Head on to the documentation](./build/index.md) to dive deeper into **investigraph**.
