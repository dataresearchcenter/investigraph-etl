# Command line

!!! info "Release notes"
    Since **investigraph 0.7** the command line interface is the only way to trigger workflow runs. Prior versions used [prefect.io](https://prefect.io) and its GUI for scheduling workflows, but we decided to simplify the stack and dropped `prefect` completely. Workflow orchestration, automated triggering or scheduling and monitoring of pipeline runs should be handled by an external framework, e.g. [Github Actions](./actions.md)

## Specify config.yml

Either use the `-c` argument for each command to specify the dataset config to use, or set it globally via this environment var:

    INVESTIGRAPH_CONFIG=./path/to/config.yml

## Run a pipeline

    investigraph run -c ./path/to/config.yml

### Options

| Option | Description | Example |
| ------ | ----------- | ------- |
| `--entities-uri` | Uri to export entities | s3://my_data/dataset/entities.ftm.json |
| `--index-uri` | Uri to export dataset metadata | s3://my_data/dataset/index.json |

## Run specific stages

The _seed_, _extract_, _transform_ and _load_ stages can be executed separately in a chained manner. This allows [parallelization](parallelization.md) of the tasks.

!!! tip
    To avoid repetitive `-c ./path/to/config.yml` flag, set the config file globally via environment variable `INVESTIGRAPH_CONFIG`.

All stages commands share these options:

| Option | Description | Example | Default |
| ------ | ----------- | ------- | ------- |
| `-c` | Path to dataset config | ./path/to/config.yml | _required_ (or via `ENV`) |
| `-i` | Input uri from previous stage | s3://remote/records.json | - (stdin) |
| `-o` | Output uri for results | s3://remote/entities.ftm.json | - (stdout) |


### Seed

This outputs [`Source`][investigraph.model.Source] objects created by the _seed_ stage as json:

    investigraph seed -c ./path/to/config.yml

### Extract

This outputs records createdy be the _extract_ stage as json:

    investigraph extract -c ./path/to/config.yml

Take seeded sources from previous _seed_ stage:

    investigraph seed | investigraph extract --from-stdin

### Transform

Pipe extracted records to transform stage:

    investigraph extract | investigraph transform

### Load

Piping the whole pipeline:

    investigraph extract | investigraph transform | investigraph load

## Inspect dataset configuration

[See tutorial](../tutorial.md)

    investigraph inspect -c ./path/to/config.yml

## Full reference

[Full reference](../reference/cli.md)
