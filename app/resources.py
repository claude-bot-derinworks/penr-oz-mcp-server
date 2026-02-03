"""Resource definitions for the MCP server."""

from pydantic import ValidationError
from app.filesystem import read_file, PathValidationError
from app.models import OzfsResourceInput
from app.errors import format_validation_error


def info() -> str:
    """Basic server info."""
    return "penr-oz MCP server"


def ozfs_resource(path: str) -> str:
    """
    Read-only file access via ozfs:// protocol.

    Args:
        path: File path within sandbox (extracted from ozfs://{path})

    Returns:
        File contents as text

    Raises:
        ValueError: If input validation fails
        PathValidationError: If path attempts to escape sandbox
        FileNotFoundError: If file doesn't exist
        IsADirectoryError: If path is a directory
    """
    # Remove leading slash if present
    if path.startswith('/'):
        path = path[1:]

    try:
        validated = OzfsResourceInput(path=path)
    except ValidationError as e:
        raise ValueError(format_validation_error(e)) from e

    return read_file(validated.path)
