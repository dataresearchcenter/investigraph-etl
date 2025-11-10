[![investigraph on pypi](https://img.shields.io/pypi/v/investigraph)](https://pypi.org/project/investigraph/)
[![Python test and package](https://github.com/dataresearchcenter/investigraph-etl/actions/workflows/python.yml/badge.svg)](https://github.com/dataresearchcenter/investigraph-etl/actions/workflows/python.yml)
[![Build docker container](https://github.com/dataresearchcenter/investigraph-etl/actions/workflows/build-docker.yml/badge.svg)](https://github.com/dataresearchcenter/investigraph-etl/actions/workflows/build-docker.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Coverage Status](https://coveralls.io/repos/github/dataresearchcenter/investigraph-etl/badge.svg?branch=main)](https://coveralls.io/github/dataresearchcenter/investigraph-etl?branch=main)
[![MIT License](https://img.shields.io/pypi/l/investigraph)](https://github.com/dataresearchcenter/investigraph-etl/blob/main/LICENSE)

# Investigraph

**investigraph** is a framework for building [datasets](./concepts/dataset.md) for [FollowTheMoney](https://followthemoney.tech) data.

[Head over to the tutorial](./tutorial.md)

## About

**investigraph** is an [ETL](https://en.wikipedia.org/wiki/Extract,_transform,_load) framework that allows research teams to build their own data catalog themselves as easily and reproducible as possible. The **investigraph** framework provides logic for *extracting*, *transforming* and *loading* any data source into [followthemoney entities](https://followthemoney.tech/).

For most common data source formats, this process is possible without programming knowledge, by means of an easy `yaml` specification interface. However, if it turns out that a specific dataset can not be parsed with the built-in logic, a developer can plug in *custom python scripts* at specific places within the pipeline to fulfill even the most edge cases in data processing.

### Features
- Create datasets in the format for [OpenAleph](https://openaleph.org)
- Cached remote source fetching and archiving of sources
- Data extraction based on `pandas` ([runpandarun](https://github.com/simonwoerpel/runpandarun))
- Data patching via [datapatch](https://github.com/pudo/datapatch)
- Transforming data records into [followthemoney](https://followthemoney.tech) entities via `yaml` mappings
- Loading result data into a various range of targets, including cloud storage (via [fsspec](https://filesystem-spec.readthedocs.io/en/latest/index.html)) or FtM stores (via [ftmq](https://docs.investigraph.dev/lib/ftmq))
- "Bring your own code" and plug it in into the right stage if the built-in logic doesn't fit your use case

### Value for investigative research teams
- standardized process to convert different data sets into a [uniform and thus comparable format](https://followthemoney.tech)
- control of this process for non-technical people
- Creation of an own (internal) data catalog
- Regular, automatic updates of the data
- A growing community that makes more and more data sets accessible
- Access to a public (open source) data library operated by the [Data and Research Center](https://dataresearchcenter.org/library) and [OpenSanctions](https://opensanctions.org/datasets)

## Github repositories
- [investigraph-etl](https://github.com/dataresearchcenter/investigraph-etl) - ETL pipeline framework for FollowTheMoney data
- [investigraph-eu](https://github.com/dataresearchcenter/investigraph-eu) - Catalog of european datasets powered by investigraph
- [runpandarun](https://github.com/simonwoerpel/runpandarun) - A simple interface written in python for reproducible i/o workflows around tabular data via [pandas](https://pandas.pydata.org/)
- [ftmq](https://github.com/dataresearchcenter/ftmq) - An attempt towards a [followthemoney](https://github.com/alephdata/followthemoney) query dsl
- [investigraph-datasets](https://github.com/dataresearchcenter/investigraph-datasets) - Example datasets configuration
- [investigraph-site](https://github.com/dataresearchcenter/investigraph-site) - Landing page for investigraph (next.js app)
- [investigraph-api](https://github.com/dataresearchcenter/investigraph-api) - public API instance to use as a test playground
- [ftmq-api](https://github.com/dataresearchcenter/ftmq-api) - Lightweight API that exposes a ftm store to a public endpoint.

## Supported by

In 2023, developing of **investigraph** was supported by [Media Tech Lab Bayern batch #3](https://github.com/media-tech-lab) for six months.

<a href="https://www.media-lab.de/en/programs/media-tech-lab">
    <img src="https://raw.githubusercontent.com/media-tech-lab/.github/main/assets/mtl-powered-by.png" width="240" title="Media Tech Lab powered by logo">
</a>
