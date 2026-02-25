"""Central configuration for the MCP server."""

import logging
import os
from pathlib import Path

SERVER_NAME = "penr-oz-mcp-server"
VERSION = "0.1.0"
ENVIRONMENT = "development"

# Filesystem sandbox configuration
PROJECT_ROOT = Path(__file__).parent.parent
SANDBOX_ROOT = PROJECT_ROOT / "sandbox"

# Debug / logging configuration
DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO


def setup_logging() -> None:
    """Configure root logging for the MCP server.

    In normal mode INFO and above are emitted.
    When the DEBUG environment variable is set to a truthy value (1/true/yes)
    the level drops to DEBUG for increased verbosity.
    """
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        force=True,
    )
