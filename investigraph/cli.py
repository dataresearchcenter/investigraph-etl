from typing import Annotated, Optional

import typer
from anystore.cli import ErrorHandler
from anystore.io import IOFormat, smart_stream_data, smart_write, smart_write_data
from anystore.logging import configure_logging, get_logger
from ftmq.io import smart_write_proxies
from rich import print

from investigraph.inspect import inspect_config
from investigraph.logic.transform import transform_record
from investigraph.model.context import get_dataset_context
from investigraph.pipeline import run
from investigraph.settings import VERSION, Settings

settings = Settings()
cli = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=settings.debug)
log = get_logger(__name__)


@cli.callback(invoke_without_command=True)
def cli_version(
    version: Annotated[Optional[bool], typer.Option(..., help="Show version")] = False
):
    if version:
        print(VERSION)
        raise typer.Exit()
    configure_logging()


@cli.command("run")
def cli_run(
    config: Annotated[
        str,
        typer.Option("-c", help="Any local or remote json or yaml uri"),
    ],
    store_uri: Annotated[Optional[str], typer.Option(...)] = None,
    index_uri: Annotated[Optional[str], typer.Option(...)] = None,
    entities_uri: Annotated[Optional[str], typer.Option(...)] = None,
):
    """
    Execute a dataset pipeline
    """
    print(
        run(config, store_uri=store_uri, entities_uri=entities_uri, index_uri=index_uri)
    )


@cli.command("extract")
def cli_extract(
    config: Annotated[
        str,
        typer.Option("-c", help="Any local or remote json or yaml uri"),
    ],
    out_uri: Annotated[str, typer.Option("-o")] = "-",
    output_format: Annotated[IOFormat, typer.Option()] = IOFormat.json,
):
    """
    Execute a dataset pipelines extract stage and write records to out_uri
    (default: stdout)
    """
    with ErrorHandler():
        ctx = get_dataset_context(config)
        smart_write_data(out_uri, ctx.extract_all(), output_format=output_format.name)


@cli.command("transform")
def cli_transform(
    config: Annotated[
        str,
        typer.Option("-c", help="Any local or remote json or yaml uri"),
    ],
    in_uri: Annotated[str, typer.Option("-i")] = "-",
    out_uri: Annotated[str, typer.Option("-o")] = "-",
    input_format: Annotated[IOFormat, typer.Option()] = IOFormat.json,
):
    """
    Execute a dataset pipelines transform stage with records from in_uri
    (default: stdin) and write proxies to out_uri (default: stdout)
    """
    with ErrorHandler():

        def _proxies():
            for ix, record in enumerate(
                smart_stream_data(in_uri, input_format=input_format.name)
            ):
                yield from transform_record(config, record, ix)

        smart_write_proxies(out_uri, _proxies())


@cli.command("inspect")
def cli_inspect(
    config: Annotated[
        str,
        typer.Option("-c", help="Any local or remote json or yaml uri"),
    ],
):
    """Validate dataset config"""
    with ErrorHandler():
        result = inspect_config(config)
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
    if out_uri == "-":
        print(settings)
    else:
        smart_write(out_uri, settings.model_dump_json().encode())
