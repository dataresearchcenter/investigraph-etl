from typing import Annotated, Optional, TypeAlias

import typer
from anystore.cli import ErrorHandler
from anystore.io import (
    IOFormat,
    smart_stream_data,
    smart_stream_json_models,
    smart_write,
    smart_write_data,
    smart_write_models,
)
from anystore.logging import configure_logging, get_logger
from anystore.types import Uri
from followthemoney import StatementEntity
from ftmq.io import smart_read_proxies, smart_write_proxies
from rich import print

from investigraph.exceptions import ImproperlyConfigured
from investigraph.inspect import inspect_config
from investigraph.logic.transform import transform_record
from investigraph.model.context import get_dataset_context, get_source_context
from investigraph.model.source import Source
from investigraph.pipeline import run
from investigraph.settings import VERSION, Settings

settings = Settings()
cli = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=settings.debug)
log = get_logger(__name__)

CONFIG_URI: TypeAlias = Annotated[
    str | None,
    typer.Option("-c", help="Any local or remote json or yaml uri"),
]


class ConfigUri(ErrorHandler):
    def __init__(self, config_uri: Uri | None = None, *args, **kwargs):
        uri = config_uri or settings.config
        if not uri:
            raise ImproperlyConfigured("Specify config.yml either via `-c` flag or ENV")
        self.config_uri = uri
        super().__init__(*args, **kwargs)

    def __enter__(self):
        return self.config_uri


@cli.callback(invoke_without_command=True)
def cli_version(
    version: Annotated[Optional[bool], typer.Option(..., help="Show version")] = False,
):
    if version:
        print(VERSION)
        raise typer.Exit()
    configure_logging()


@cli.command("run")
def cli_run(
    config: CONFIG_URI = None,
    store_uri: Annotated[Optional[str], typer.Option(...)] = None,
    index_uri: Annotated[Optional[str], typer.Option(...)] = None,
    entities_uri: Annotated[Optional[str], typer.Option(...)] = None,
):
    """
    Execute a dataset pipeline
    """
    with ConfigUri(config) as config_uri:
        print(
            run(
                config_uri,
                store_uri=store_uri,
                entities_uri=entities_uri,
                index_uri=index_uri,
            )
        )


@cli.command("seed")
def cli_seed(
    config: CONFIG_URI = None,
    out_uri: Annotated[str, typer.Option("-o")] = "-",
    output_format: Annotated[IOFormat, typer.Option()] = IOFormat.json,
    limit: Annotated[
        int | None,
        typer.Option("-l", help="Only get this number of items"),
    ] = None,
):
    """
    Execute a dataset pipelines seed stage and write sources to out_uri
    (default: stdout)
    """
    with ConfigUri(config) as config_uri:
        ctx = get_dataset_context(config_uri)
        sources = (c.source for c in ctx.get_sources(limit))
        smart_write_models(out_uri, sources, output_format=output_format.name)


@cli.command("extract")
def cli_extract(
    config: CONFIG_URI = None,
    source: Annotated[
        str | None, typer.Option("-s", help="Source name (from config)")
    ] = None,
    from_stdin: Annotated[bool, typer.Option()] = False,
    out_uri: Annotated[str, typer.Option("-o")] = "-",
    output_format: Annotated[IOFormat, typer.Option()] = IOFormat.json,
    limit: Annotated[
        int | None,
        typer.Option("-l", help="Only get this number of items"),
    ] = None,
):
    """
    Execute a dataset pipelines extract stage and write records to out_uri
    (default: stdout)
    """
    with ConfigUri(config) as config_uri:
        if from_stdin:
            for source_ in smart_stream_json_models("-", Source):
                if source is None or source == source_.name:
                    ctx = get_source_context(config_uri, source_.name, uri=source_.uri)
                    smart_write_data(
                        out_uri, ctx.extract(limit), output_format=output_format.name
                    )
        else:
            extractor = []
            ctx = get_dataset_context(config_uri)
            if source is not None:
                for sctx in ctx.get_sources():
                    if sctx.source.name == source:
                        extractor = sctx.extract(limit)
                        break
            else:
                extractor = ctx.extract_all(limit)
            smart_write_data(out_uri, extractor, output_format=output_format.name)


@cli.command("transform")
def cli_transform(
    config: CONFIG_URI = None,
    in_uri: Annotated[str, typer.Option("-i")] = "-",
    out_uri: Annotated[str, typer.Option("-o")] = "-",
    input_format: Annotated[IOFormat, typer.Option()] = IOFormat.json,
):
    """
    Execute a dataset pipelines transform stage with records from in_uri
    (default: stdin) and write proxies to out_uri (default: stdout)
    """
    with ConfigUri(config) as config_uri:

        def _proxies():
            for ix, record in enumerate(
                smart_stream_data(in_uri, input_format=input_format.name)
            ):
                yield from transform_record(config_uri, record, ix)

        smart_write_proxies(out_uri, _proxies())


@cli.command("load")
def cli_load(
    config: CONFIG_URI = None,
    in_uri: Annotated[str, typer.Option("-i")] = "-",
):
    """
    Execute a dataset pipelines load stage with proxies from in_uri
    (default: stdin)
    """
    with ConfigUri(config) as config_uri:
        proxies = smart_read_proxies(in_uri, entity_type=StatementEntity)
        ctx = get_dataset_context(config_uri)
        ctx.load(proxies)


@cli.command("inspect")
def cli_inspect(config: CONFIG_URI = None):
    """Validate dataset config"""
    with ConfigUri(config) as config_uri:
        result = inspect_config(config_uri)
        print(f"[bold green]OK[/bold green] `{config}`")
        print(f"[bold]dataset:[/bold] {result.dataset.name}")
        print(f"[bold]title:[/bold] {result.dataset.title}")


@cli.command("settings")
def cli_settings(
    out_uri: Annotated[str, typer.Option("-o")] = "-",
):
    """
    Show current settings
    """
    with ErrorHandler():
        if out_uri == "-":
            print(settings)
        else:
            smart_write(out_uri, settings.model_dump_json().encode())
