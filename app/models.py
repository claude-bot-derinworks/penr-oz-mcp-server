"""Pydantic models for structured validation of all MCP tools and resources."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# --- Tool Input Models ---


class PingInput(BaseModel):
    """Input model for the ping health-check tool (no parameters)."""

    model_config = {"json_schema_extra": {"examples": [{}]}}


class ListFilesInput(BaseModel):
    """Input model for the list_files tool."""

    path: str = Field(
        default="",
        description="Relative path within sandbox (default: root directory)",
        examples=["", "docs", "data"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"path": ""}, {"path": "docs"}, {"path": "data"}]
        }
    }


class ReadTextFileInput(BaseModel):
    """Input model for the read_text_file tool."""

    path: str = Field(
        description="Relative path to file within sandbox",
        min_length=1,
        examples=["welcome.txt", "docs/guide.md", "data/sample.json"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"path": "welcome.txt"},
                {"path": "docs/guide.md"},
            ]
        }
    }


class FetchJsonInput(BaseModel):
    """Input model for the fetch_json API tool."""

    url: str = Field(
        description="The HTTP(S) URL to fetch JSON from",
        min_length=1,
        examples=["https://api.github.com/repos/python/cpython"],
    )
    timeout: float = Field(
        default=10.0,
        description="Request timeout in seconds",
        gt=0,
        le=300,
        examples=[10.0, 5.0, 30.0],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"url": "https://api.github.com/repos/python/cpython"},
                {"url": "https://api.example.com/data", "timeout": 5.0},
            ]
        }
    }


class OzfsResourceInput(BaseModel):
    """Input model for the ozfs:// resource."""

    path: str = Field(
        description="File path within sandbox (extracted from ozfs://{path})",
        min_length=1,
        examples=["welcome.txt", "docs/guide.md"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"path": "welcome.txt"},
                {"path": "docs/guide.md"},
            ]
        }
    }


# --- Tool Output Models ---


class FileEntry(BaseModel):
    """A single file or directory entry in a listing."""

    name: str = Field(description="Name of the file or directory")
    type: str = Field(description="Entry type: 'file' or 'directory'")
    path: str = Field(description="Relative path within sandbox")
    size: Optional[int] = Field(
        default=None,
        description="File size in bytes (only for files)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "welcome.txt",
                    "type": "file",
                    "path": "welcome.txt",
                    "size": 128,
                },
                {
                    "name": "docs",
                    "type": "directory",
                    "path": "docs",
                    "size": None,
                },
            ]
        }
    }


class ListFilesOutput(BaseModel):
    """Output model for the list_files tool."""

    entries: List[FileEntry] = Field(
        description="List of file and directory entries"
    )
