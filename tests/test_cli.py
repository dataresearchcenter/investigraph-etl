from pathlib import Path

from typer.testing import CliRunner

from investigraph.cli import cli

runner = CliRunner()


def test_cli_base():
    result = runner.invoke(cli, "--help")
    assert result.exit_code == 0


def test_cli_run(fixtures_path: Path):
    config = str(fixtures_path / "gdho" / "config.local.yml")
    result = runner.invoke(cli, ["run", "-c", config])
    assert result.exit_code == 0

    # no arguments
    result = runner.invoke(cli, ["run"])
    assert result.exit_code > 0


def test_cli_inspect(fixtures_path: Path):
    config = str(fixtures_path / "gdho" / "config.local.yml")
    result = runner.invoke(cli, ["inspect", "-c", config])
    assert result.exit_code == 0


def test_cli_seed(fixtures_path: Path):
    config = str(fixtures_path / "config.seed.yml")
    result = runner.invoke(cli, ["seed", "-c", config, "-l", "10"])
    assert result.exit_code == 0


def test_cli_extract(fixtures_path: Path):
    config = str(fixtures_path / "gdho" / "config.local.yml")
    result = runner.invoke(cli, ["extract", "-c", config, "-l", "10"])
    assert result.exit_code == 0


def test_cli_transform(fixtures_path: Path):
    config = str(fixtures_path / "gdho" / "config.local.yml")
    result = runner.invoke(cli, ["transform", "-c", config])
    assert result.exit_code == 0


def test_cli_load(fixtures_path: Path):
    config = str(fixtures_path / "gdho" / "config.local.yml")
    result = runner.invoke(cli, ["load", "-c", config])
    assert result.exit_code == 0
