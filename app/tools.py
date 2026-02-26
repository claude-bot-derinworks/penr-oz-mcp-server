"""Tool definitions for the MCP server."""

import logging
from typing import List, Dict
from pydantic import ValidationError
from app.filesystem import list_directory, read_file, PathValidationError
from app.models import ListFilesInput, ReadTextFileInput
from app.errors import format_validation_error

logger = logging.getLogger(__name__)


def ping() -> str:
    """Health check tool."""
    logger.debug("Tool invoked: ping")
    return "pong"


def list_files(path: str = "") -> List[Dict[str, str]]:
    """
    List files and directories within the sandbox.

    Args:
        path: Relative path within sandbox (default: root directory)

    Returns:
        List of file/directory entries with metadata

    Raises:
        ValueError: If input validation fails
        PathValidationError: If path attempts to escape sandbox
        FileNotFoundError: If directory doesn't exist
        NotADirectoryError: If path is not a directory
    """
    try:
        validated = ListFilesInput(path=path)
    except ValidationError as e:
        msg = format_validation_error(e)
        logger.error("Tool list_files validation failed for path=%r: %s", path, msg)
        raise ValueError(msg) from e

    logger.debug("Tool invoked: list_files path=%r", validated.path)
    try:
        result = list_directory(validated.path)
        logger.info("Tool list_files succeeded: %d entries for path=%r", len(result), validated.path)
        return result
    except (PathValidationError, FileNotFoundError, NotADirectoryError) as e:
        logger.error("Tool list_files failed for path=%r", validated.path, exc_info=True)
        raise


def read_text_file(path: str) -> str:
    """
    Read text content from a file within the sandbox.

    Args:
        path: Relative path to file within sandbox

    Returns:
        File contents as text

    Raises:
        ValueError: If input validation fails
        PathValidationError: If path attempts to escape sandbox
        FileNotFoundError: If file doesn't exist
        IsADirectoryError: If path is a directory
        UnicodeDecodeError: If file is not valid UTF-8 text
    """
    try:
        validated = ReadTextFileInput(path=path)
    except ValidationError as e:
        msg = format_validation_error(e)
        logger.error("Tool read_text_file validation failed for path=%r: %s", path, msg)
        raise ValueError(msg) from e

    logger.debug("Tool invoked: read_text_file path=%r", validated.path)
    try:
        result = read_file(validated.path)
        logger.info("Tool read_text_file succeeded: %d bytes for path=%r", len(result), validated.path)
        return result
    except (PathValidationError, FileNotFoundError, IsADirectoryError, UnicodeDecodeError) as e:
        logger.error("Tool read_text_file failed for path=%r", validated.path, exc_info=True)
        raise
