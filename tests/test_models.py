"""Tests for Pydantic validation models and centralized error handling."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models import (
    PingInput,
    ListFilesInput,
    ReadTextFileInput,
    FetchJsonInput,
    OzfsResourceInput,
    FileEntry,
    ListFilesOutput,
)
from app.errors import (
    format_validation_error,
    extract_error_details,
    ValidationErrorDetail,
)


# --- Input Model Tests ---


class TestPingInput:
    """Test PingInput model."""

    def test_ping_input_no_params(self):
        """PingInput accepts no parameters."""
        model = PingInput()
        assert model is not None


class TestListFilesInput:
    """Test ListFilesInput model."""

    def test_default_path(self):
        """Default path should be empty string."""
        model = ListFilesInput()
        assert model.path == ""

    def test_valid_path(self):
        """Valid paths should be accepted."""
        model = ListFilesInput(path="docs")
        assert model.path == "docs"

    def test_nested_path(self):
        """Nested paths should be accepted."""
        model = ListFilesInput(path="docs/subdir")
        assert model.path == "docs/subdir"

    def test_empty_path(self):
        """Empty path should be accepted (root listing)."""
        model = ListFilesInput(path="")
        assert model.path == ""


class TestReadTextFileInput:
    """Test ReadTextFileInput model."""

    def test_valid_path(self):
        """Valid file path should be accepted."""
        model = ReadTextFileInput(path="welcome.txt")
        assert model.path == "welcome.txt"

    def test_nested_path(self):
        """Nested file path should be accepted."""
        model = ReadTextFileInput(path="docs/guide.md")
        assert model.path == "docs/guide.md"

    def test_empty_path_rejected(self):
        """Empty path should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReadTextFileInput(path="")
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_missing_path_rejected(self):
        """Missing path should be rejected."""
        with pytest.raises(ValidationError):
            ReadTextFileInput()


class TestFetchJsonInput:
    """Test FetchJsonInput model."""

    def test_valid_https_url(self):
        """Valid HTTPS URL should be accepted."""
        model = FetchJsonInput(url="https://api.example.com/data")
        assert model.url == "https://api.example.com/data"
        assert model.timeout == 10.0

    def test_valid_http_url(self):
        """Valid HTTP URL should be accepted."""
        model = FetchJsonInput(url="http://api.example.com/data")
        assert model.url == "http://api.example.com/data"

    def test_custom_timeout(self):
        """Custom timeout should be accepted."""
        model = FetchJsonInput(url="https://api.example.com", timeout=5.0)
        assert model.timeout == 5.0

    def test_empty_url_rejected(self):
        """Empty URL should be rejected."""
        with pytest.raises(ValidationError):
            FetchJsonInput(url="")

    def test_missing_url_rejected(self):
        """Missing URL should be rejected."""
        with pytest.raises(ValidationError):
            FetchJsonInput()

    def test_zero_timeout_rejected(self):
        """Zero timeout should be rejected (must be > 0)."""
        with pytest.raises(ValidationError):
            FetchJsonInput(url="https://api.example.com", timeout=0)

    def test_negative_timeout_rejected(self):
        """Negative timeout should be rejected."""
        with pytest.raises(ValidationError):
            FetchJsonInput(url="https://api.example.com", timeout=-1.0)

    def test_excessive_timeout_rejected(self):
        """Timeout exceeding 300s should be rejected."""
        with pytest.raises(ValidationError):
            FetchJsonInput(url="https://api.example.com", timeout=301.0)

    def test_default_timeout(self):
        """Default timeout should be 10.0."""
        model = FetchJsonInput(url="https://api.example.com")
        assert model.timeout == 10.0


class TestOzfsResourceInput:
    """Test OzfsResourceInput model."""

    def test_valid_path(self):
        """Valid path should be accepted."""
        model = OzfsResourceInput(path="welcome.txt")
        assert model.path == "welcome.txt"

    def test_nested_path(self):
        """Nested path should be accepted."""
        model = OzfsResourceInput(path="docs/guide.md")
        assert model.path == "docs/guide.md"

    def test_empty_path_rejected(self):
        """Empty path should be rejected."""
        with pytest.raises(ValidationError):
            OzfsResourceInput(path="")

    def test_missing_path_rejected(self):
        """Missing path should be rejected."""
        with pytest.raises(ValidationError):
            OzfsResourceInput()


# --- Output Model Tests ---


class TestFileEntry:
    """Test FileEntry output model."""

    def test_file_entry(self):
        """File entry should include all fields."""
        entry = FileEntry(
            name="welcome.txt", type="file", path="welcome.txt", size=128
        )
        assert entry.name == "welcome.txt"
        assert entry.type == "file"
        assert entry.path == "welcome.txt"
        assert entry.size == 128

    def test_directory_entry(self):
        """Directory entry should have size as None."""
        entry = FileEntry(name="docs", type="directory", path="docs")
        assert entry.name == "docs"
        assert entry.type == "directory"
        assert entry.size is None

    def test_file_entry_serialization(self):
        """FileEntry should serialize to dict correctly."""
        entry = FileEntry(
            name="test.txt", type="file", path="test.txt", size=42
        )
        data = entry.model_dump()
        assert data["name"] == "test.txt"
        assert data["type"] == "file"
        assert data["size"] == 42


class TestListFilesOutput:
    """Test ListFilesOutput model."""

    def test_output_with_entries(self):
        """Output model should hold list of entries."""
        entries = [
            FileEntry(name="a.txt", type="file", path="a.txt", size=10),
            FileEntry(name="docs", type="directory", path="docs"),
        ]
        output = ListFilesOutput(entries=entries)
        assert len(output.entries) == 2

    def test_empty_entries(self):
        """Output model should accept empty list."""
        output = ListFilesOutput(entries=[])
        assert len(output.entries) == 0


# --- Centralized Error Handling Tests ---


class TestValidationErrorDetail:
    """Test ValidationErrorDetail."""

    def test_to_dict(self):
        """Detail should convert to dict."""
        detail = ValidationErrorDetail(field="url", message="required")
        result = detail.to_dict()
        assert result["field"] == "url"
        assert result["message"] == "required"

    def test_to_dict_with_value(self):
        """Detail with value should include it in dict."""
        detail = ValidationErrorDetail(field="timeout", message="too large", value=999)
        result = detail.to_dict()
        assert result["value"] == 999

    def test_to_dict_without_value(self):
        """Detail without value should omit it from dict."""
        detail = ValidationErrorDetail(field="url", message="required")
        result = detail.to_dict()
        assert "value" not in result


class TestFormatValidationError:
    """Test format_validation_error function."""

    def test_format_single_error(self):
        """Single validation error should be formatted."""
        try:
            ReadTextFileInput(path="")
        except ValidationError as e:
            result = format_validation_error(e)
            assert "Validation error" in result
            assert "1 issue(s)" in result
            assert "path" in result

    def test_format_multiple_errors(self):
        """Multiple validation errors should be formatted."""
        try:
            FetchJsonInput(url="", timeout=-1)
        except ValidationError as e:
            result = format_validation_error(e)
            assert "Validation error" in result
            assert "issue(s)" in result


class TestExtractErrorDetails:
    """Test extract_error_details function."""

    def test_extract_from_validation_error(self):
        """Should extract structured details from ValidationError."""
        try:
            ReadTextFileInput(path="")
        except ValidationError as e:
            details = extract_error_details(e)
            assert len(details) > 0
            assert details[0].field == "path"

    def test_extract_preserves_input_value(self):
        """Extracted details should include the invalid input value."""
        try:
            FetchJsonInput(url="https://example.com", timeout=-5)
        except ValidationError as e:
            details = extract_error_details(e)
            timeout_detail = [d for d in details if "timeout" in d.field]
            assert len(timeout_detail) > 0
            assert timeout_detail[0].value == -5


# --- Integration: Tool-level validation ---


class TestToolValidationIntegration:
    """Test that tools raise proper errors for invalid input."""

    def test_read_text_file_empty_path(self):
        """read_text_file should raise ValueError for empty path."""
        from app.tools import read_text_file

        with pytest.raises(ValueError, match="Validation error"):
            read_text_file("")

    def test_list_files_valid_default(self):
        """list_files with default should work (no validation error)."""
        from app.tools import list_files

        result = list_files()
        assert isinstance(result, list)

    def test_fetch_json_empty_url(self):
        """fetch_json should raise InvalidURLError for empty URL."""
        import asyncio
        from app.api import fetch_json, InvalidURLError

        with pytest.raises(InvalidURLError, match="Validation error"):
            asyncio.run(fetch_json(""))

    def test_fetch_json_negative_timeout(self):
        """fetch_json should raise InvalidURLError for negative timeout."""
        import asyncio
        from app.api import fetch_json, InvalidURLError

        with pytest.raises(InvalidURLError, match="Validation error"):
            asyncio.run(fetch_json("https://example.com", timeout=-1))

    def test_ozfs_resource_empty_path(self):
        """ozfs_resource should raise ValueError for empty path after slash strip."""
        from app.resources import ozfs_resource

        with pytest.raises(ValueError, match="Validation error"):
            ozfs_resource("")
