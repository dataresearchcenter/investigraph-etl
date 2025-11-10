# Parallelization

!!! info "Release notes"
    Since **investigraph 0.7** the command line interface is the only way to trigger workflow runs. Prior versions used [prefect.io](https://prefect.io) to enable multiple workers for parallel processing, but we decided to simplify the stack and dropped `prefect` completely.

As the different stages of a pipeline can be executed separately via the [command line ](./cli.md) and use streaming input / output, parallelization (multi-processing) of tasks is possible with a 3rd party tool, for example [GNU Parallel](https://www.gnu.org/software/parallel/sphinx.html)


!!! tip
    To avoid repetitive `-c ./path/to/config.yml` flag, set the config file globally via environment variable `INVESTIGRAPH_CONFIG`.


## Run a complete pipeline in parallel

    investigraph extract | parallel --pipe investigraph transform | parallel --pipe investigraph load

!!! warning "Use shared stores that can handle parallel writes"
    - When using the `load` stage together with `parallel` as in the example above, make sure the FollowTheMoney store can handle parallel writes (e.g. postgres)
    - Don't rely on the default in-memory runtime cache. If you need caching (e.g. storing intermediate contextual data during runtime), set a proper shared cache via the environment `INVESTIGRAPH_CACHE_URI` (e.g. `redis://localhost`)

## Tweaking

- Use `-j` flag for number of processes to spawn (defaults to all threads)
- Use `-N` flag for batch size
- Use `--roundrobin`
