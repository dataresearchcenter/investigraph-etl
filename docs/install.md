# Install

Installing investigraph is needed for interactive development of new dataset sources or local test runs, though.

!!! tip
    It is highly recommended to use a [python virtual environment](https://learnpython.com/blog/how-to-use-virtualenv-python/) for installation.

investigraph ships as a python package and can easily be installed via pip (or any other package manager from the python ecosystem):

    pip install investigraph

After installation and all it's dependencies, check that it is working:

    investigraph --version

Upgrade the package to the latest version:

    pip install -U investigraph

Uninstall:

    pip uninstall investigraph

## Extra dependencies

To write [entities](./concepts/entity.md) to a specific store backend, some extra dependencies need to be installed:

### Sql(ite)

    pip install investigraph[sql]

### Postgresql

    pip install investigraph[postgres]

### LevelDB

This might require some system packages, [check out leveldb documentation](https://plyvel.readthedocs.io/en/latest/installation.html).

    pip install investigraph[level]

### Redis or KVRocks

    pip install investigraph[redis]

## Develop version

Active development is happening in the `develop` branch. You can directly install it via pip:

    pip install git+https://github.com/dataresearchcenter/investigraph-etl.git@develop
