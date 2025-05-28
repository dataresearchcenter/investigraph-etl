"""
Inspect dataset pipeline config
"""

from anystore.logging import get_logger
from anystore.types import Uri

from investigraph.model.config import Config, get_config

log = get_logger(__name__)


def log_error(msg: str):
    log.error(f"[bold red]ERROR[/bold red] {msg}")


def inspect_config(p: Uri) -> Config:
    config = get_config(p)
    try:
        if not callable(config.extract.get_handler()):
            log_error(f"module not found or not callable: `{config.extract.handler}`")
    except ModuleNotFoundError:
        log_error(f"no custom extract module: `{config.extract.handler}`")
    try:
        if not callable(config.transform.get_handler()):
            log_error(f"module not found or not callable: `{config.transform.handler}`")
    except ModuleNotFoundError:
        log_error(f"no custom transform module: `{config.transform.handler}`")
    try:
        if not callable(config.load.get_handler()):
            log_error(f"module not found or not callable: `{config.load.handler}`")
    except ModuleNotFoundError:
        log_error(f"no custom load module: `{config.load.handler}`")
    return config
