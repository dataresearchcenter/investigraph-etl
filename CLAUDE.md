# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Scope: developing the **investigraph library** itself. For building *dataset scrapers*
with investigraph, see `contrib/CLAUDE.md` instead.

## Behaviour rules for code agents

1. Don’t assume. Don’t hide confusion. Surface tradeoffs.
2. Minimum code that solves the problem. Nothing speculative.
3. Touch only what you must. Clean up only your own mess.
4. Define success criteria. Loop until verified.


## Environment

- Always use the virtualenv at `.venv` for running Python, pip, pytest, etc.
- Activate with `source .venv/bin/activate` or use `.venv/bin/python` directly.
- The CLI is a console script: `.venv/bin/investigraph`. There is no
  `investigraph/__main__.py`, so `python -m investigraph` does **not** work.

## Common Commands

```bash
# Run tests
.venv/bin/python -m pytest tests/ -q

# Run a single test
.venv/bin/python -m pytest tests/test_extract.py::test_extract -q

# Run full pipeline via CLI
.venv/bin/investigraph run -c path/to/config.yml

# Individual stages — transform/load read records/proxies from stdin (-i),
# extract/seed write to stdout (-o)
.venv/bin/investigraph seed -c config.yml -l 10
.venv/bin/investigraph extract -c config.yml -l 10 \
  | .venv/bin/investigraph transform -c config.yml \
  | .venv/bin/investigraph load -c config.yml

# Validate a config / show settings
.venv/bin/investigraph inspect -c config.yml
.venv/bin/investigraph settings

# Linting (config in setup.cfg: max-line-length 88, extend-ignore E203,E501)
.venv/bin/python -m flake8 investigraph/
.venv/bin/python -m isort investigraph/
.venv/bin/python -m black investigraph/

# Makefile targets (run via poetry)
make install     # poetry install --with dev --all-extras
make test        # pytest with coverage, wipes .test before/after
make lint        # flake8
make typecheck   # mypy --strict investigraph
make pre-commit  # install + run all hooks
```

Dependency management is poetry. Three deps are git-pinned (`ftmq` on branch
`refactor/ql`, `memorious4`, `ftm-lakehouse`), so use `poetry install` rather
than plain pip. Optional extras: `sql`, `postgres`, `redis`, `level`.

## Architecture

**ETL pipeline for FollowTheMoney (FTM) investigative data.**

### Pipeline flow (`investigraph/pipeline.py`)

```
Config → Seed (generate sources) → Extract (records) → Transform (FTM entities) → Load (to store) → Export
```

`run()` is the entrypoint: it builds a `DatasetContext`, iterates source contexts
(extract → transform → load per source), then exports once — unless every source
was cached/skipped. Each stage is config-driven and pluggable via handler strings
(e.g. `investigraph.logic.extract:handle`), defaulting to the values in
`Settings` (`seeder`, `extractor`, `transformer`, `loader`, `exporter`).

### Key modules

- **`investigraph/model/context.py`** — Core runtime contexts: `DatasetContext`, `SourceContext`, `TaskContext`. These wrap config and provide stage execution, caching, entity creation helpers (`make_entity`, `make_slug`, `make_id`, `make_fingerprint_id`), fetching and file I/O.
- **`investigraph/model/config.py`** — Config loading from YAML/JSON URIs. Defines `Config` with nested stage configs.
- **`investigraph/model/stage.py`** — `Stage` base plus `SeedStage`, `ExtractStage`, `TransformStage`, `LoadStage`, `ExportStage` (handler resolution, per-stage options).
- **`investigraph/model/source.py`** — `Source` model for local/remote data sources.
- **`investigraph/model/mapping.py`** — YAML `transform.queries` mappings (`QueryMapping`, `EntityMapping`, `PropertyMapping`) bridged to followthemoney mappings.
- **`investigraph/logic/`** — Default handlers for each pipeline stage (seed, extract, transform, load, export) plus `fetch.py` (memorious/lakehouse archive fetching, incremental tags).
- **`investigraph/helpers/`** — Reusable transform helpers, currently address formatting (`format_address`, `make_address`, `assign_address`).
- **`investigraph/inspect.py`** — Config validation used by `investigraph inspect`.
- **`investigraph/settings.py`** — Pydantic settings with `INVESTIGRAPH_` env prefix. Aliased exceptions without the prefix: `DEBUG`, `FTM_STATEMENT_STORE` (→ `store_uri`), `LAKEHOUSE_URI`.
- **`investigraph/cli.py`** — Typer CLI with commands: `run`, `seed`, `extract`, `transform`, `load`, `inspect`, `settings`.

### Dependencies

- **anystore** — Storage abstraction (local, S3, memory, etc.) and caching
- **memorious** — HTTP fetching with archive, caching, stealthy mode (used lazily in `SourceContext.open()`)
- **ftmq / followthemoney** — Entity model, statement stores, aggregation
- **runpandarun** — Pandas-based data extraction with playbooks
- **ftm-lakehouse** — Content-addressed archive (via memorious)
- **rigour, dateparser** — Normalization and date parsing helpers

### Testing

Tests use a local HTTP server fixture (port 8000) serving files from `tests/fixtures/`. Config fixtures load dataset YAML from `tests/fixtures/{ec_meetings,gdho,eu_authorities}/config.yml` and rewrite source URIs to `http://localhost:8000/...`. `pytest-xdist` is available for parallel runs.

Env vars set during tests come from `pyproject.toml [tool.pytest_env]`:
- `DEBUG=1`
- `INVESTIGRAPH_DATA_ROOT=.test`
- `NOMENKLATURA_DB_URL=sqlite:///:memory:`
- `FTM_STATEMENT_STORE=memory://`

Note: `pytest.ini` is the pytest configfile, but its `env =` block (`PREFECT_HOME`, `DATA_ROOT`, `DATASETS_REPO`, `TASK_CACHE`) is **not** applied — pytest-env prefers `[tool.pytest_env]` from `pyproject.toml`. Those entries are leftovers from the prefect era.
