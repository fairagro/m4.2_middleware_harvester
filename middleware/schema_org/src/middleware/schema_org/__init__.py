"""Schema.org harvester plugin package."""

from .config import Config
from .plugin import run_plugin

__all__ = ["Config", "run_plugin"]
