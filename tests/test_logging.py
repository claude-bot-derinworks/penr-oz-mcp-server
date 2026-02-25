"""Tests for structured logging and debug mode (issue #7)."""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest
import respx
import httpx


# ---------------------------------------------------------------------------
# config.py — setup_logging / DEBUG flag
# ---------------------------------------------------------------------------

class TestSetupLogging:
    @pytest.fixture(autouse=True)
    def reload_config_after_test(self):
        """Reload app.config after each test to restore default state."""
        yield
        import importlib
        import app.config as cfg
        importlib.reload(cfg)

    def test_default_level_is_info(self):
        """setup_logging() sets root log level to INFO when DEBUG is unset."""
        import importlib
        import app.config as cfg

        # Ensure DEBUG is not in the environment
        env = {k: v for k, v in os.environ.items() if k != "DEBUG"}
        with patch.dict(os.environ, env, clear=True):
            importlib.reload(cfg)
            cfg.setup_logging()
            assert cfg.LOG_LEVEL == logging.INFO

    def test_debug_flag_sets_debug_level(self):
        """DEBUG=1 lowers LOG_LEVEL to DEBUG."""
        import importlib
        import app.config as cfg

        with patch.dict(os.environ, {"DEBUG": "1"}):
            importlib.reload(cfg)
            assert cfg.DEBUG is True
            assert cfg.LOG_LEVEL == logging.DEBUG

    def test_debug_flag_true_value(self):
        """DEBUG=true is treated as a truthy value."""
        import importlib
        import app.config as cfg

        with patch.dict(os.environ, {"DEBUG": "true"}):
            importlib.reload(cfg)
            assert cfg.DEBUG is True

    def test_debug_flag_yes_value(self):
        """DEBUG=yes is treated as a truthy value."""
        import importlib
        import app.config as cfg

        with patch.dict(os.environ, {"DEBUG": "yes"}):
            importlib.reload(cfg)
            assert cfg.DEBUG is True

    def test_debug_flag_false_when_unset(self):
        """DEBUG is False when the env var is absent."""
        import importlib
        import app.config as cfg

        env = {k: v for k, v in os.environ.items() if k != "DEBUG"}
        with patch.dict(os.environ, env, clear=True):
            importlib.reload(cfg)
            assert cfg.DEBUG is False


# ---------------------------------------------------------------------------
# tools.py — ping
# ---------------------------------------------------------------------------

class TestPingLogging:
    def test_ping_emits_debug_log(self, caplog):
        """ping() emits a DEBUG-level log entry."""
        from app.tools import ping

        with caplog.at_level(logging.DEBUG, logger="app.tools"):
            ping()

        assert any("ping" in record.message for record in caplog.records)
        assert any(record.levelno == logging.DEBUG for record in caplog.records)

    def test_ping_no_sensitive_data_in_log(self, caplog):
        """ping() log must not contain any sensitive data."""
        from app.tools import ping

        with caplog.at_level(logging.DEBUG, logger="app.tools"):
            ping()

        for record in caplog.records:
            # No passwords, tokens, or secret-like strings should appear
            assert "password" not in record.message.lower()
            assert "secret" not in record.message.lower()
            assert "token" not in record.message.lower()


# ---------------------------------------------------------------------------
# tools.py — list_files
# ---------------------------------------------------------------------------

class TestListFilesLogging:
    def test_list_files_success_emits_info(self, caplog):
        """list_files() emits an INFO log on success."""
        from app.tools import list_files

        with caplog.at_level(logging.INFO, logger="app.tools"):
            list_files("")

        assert any(
            "list_files" in record.message and record.levelno == logging.INFO
            for record in caplog.records
        )

    def test_list_files_failure_emits_error(self, caplog):
        """list_files() emits an ERROR log when the path doesn't exist."""
        from app.tools import list_files

        with caplog.at_level(logging.ERROR, logger="app.tools"):
            with pytest.raises(FileNotFoundError):
                list_files("nonexistent_path_xyz")

        assert any(record.levelno == logging.ERROR for record in caplog.records)

    def test_list_files_debug_log_on_invocation(self, caplog):
        """list_files() emits a DEBUG log when called."""
        from app.tools import list_files

        with caplog.at_level(logging.DEBUG, logger="app.tools"):
            list_files("")

        assert any(
            "list_files" in record.message and record.levelno == logging.DEBUG
            for record in caplog.records
        )


# ---------------------------------------------------------------------------
# tools.py — read_text_file
# ---------------------------------------------------------------------------

class TestReadTextFileLogging:
    def test_read_text_file_failure_emits_error(self, caplog, tmp_path):
        """read_text_file() emits an ERROR log for missing files."""
        from app.tools import read_text_file

        with caplog.at_level(logging.ERROR, logger="app.tools"):
            with pytest.raises(FileNotFoundError):
                read_text_file("no_such_file.txt")

        assert any(record.levelno == logging.ERROR for record in caplog.records)

    def test_read_text_file_debug_log_on_invocation(self, caplog):
        """read_text_file() emits a DEBUG log when called."""
        from app.tools import read_text_file

        with caplog.at_level(logging.DEBUG, logger="app.tools"):
            with pytest.raises(FileNotFoundError):
                read_text_file("no_such_file.txt")

        assert any(
            "read_text_file" in record.message and record.levelno == logging.DEBUG
            for record in caplog.records
        )


# ---------------------------------------------------------------------------
# api.py — fetch_json
# ---------------------------------------------------------------------------

class TestFetchJsonLogging:
    @pytest.mark.asyncio
    async def test_fetch_json_invalid_scheme_emits_error(self, caplog):
        """fetch_json() logs an error for invalid URL schemes."""
        from app.api import fetch_json, InvalidURLError

        with caplog.at_level(logging.ERROR, logger="app.api"):
            with pytest.raises(InvalidURLError):
                await fetch_json("ftp://example.com/data.json")

        assert any(record.levelno == logging.ERROR for record in caplog.records)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_json_success_emits_info(self, respx_mock, caplog):
        """fetch_json() emits an INFO log on success."""
        respx_mock.get("https://api.example.com/data").mock(
            return_value=httpx.Response(200, json={"key": "value"})
        )

        from app.api import fetch_json

        with caplog.at_level(logging.INFO, logger="app.api"):
            await fetch_json("https://api.example.com/data")

        assert any(
            "fetch_json" in record.message and record.levelno == logging.INFO
            for record in caplog.records
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_json_http_error_emits_error(self, respx_mock, caplog):
        """fetch_json() emits an ERROR log for HTTP error responses."""
        respx_mock.get("https://api.example.com/notfound").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )

        from app.api import fetch_json, HTTPError

        with caplog.at_level(logging.ERROR, logger="app.api"):
            with pytest.raises(HTTPError):
                await fetch_json("https://api.example.com/notfound")

        assert any(record.levelno == logging.ERROR for record in caplog.records)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_json_timeout_emits_error(self, respx_mock, caplog):
        """fetch_json() emits an ERROR log on timeout."""
        respx_mock.get("https://api.example.com/slow").mock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        from app.api import fetch_json, TimeoutError

        with caplog.at_level(logging.ERROR, logger="app.api"):
            with pytest.raises(TimeoutError):
                await fetch_json("https://api.example.com/slow", timeout=1.0)

        assert any(record.levelno == logging.ERROR for record in caplog.records)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_json_no_response_body_in_logs(self, respx_mock, caplog):
        """fetch_json() must not log raw response bodies that may contain sensitive data."""
        sensitive_payload = {"api_key": "super-secret-key-xyz", "token": "bearer-abc"}
        respx_mock.get("https://api.example.com/secret").mock(
            return_value=httpx.Response(200, json=sensitive_payload)
        )

        from app.api import fetch_json

        with caplog.at_level(logging.DEBUG, logger="app.api"):
            await fetch_json("https://api.example.com/secret")

        for record in caplog.records:
            # Response body values must never appear in log messages
            assert "super-secret-key-xyz" not in record.message
            assert "bearer-abc" not in record.message

    @pytest.mark.asyncio
    async def test_fetch_json_debug_log_on_invocation(self, caplog):
        """fetch_json() emits a DEBUG log when called."""
        from app.api import fetch_json, InvalidURLError

        with caplog.at_level(logging.DEBUG, logger="app.api"):
            with pytest.raises(InvalidURLError):
                await fetch_json("")

        assert any(
            "fetch_json" in record.message and record.levelno == logging.DEBUG
            for record in caplog.records
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_json_url_query_params_not_logged(self, respx_mock, caplog):
        """fetch_json() must not log URL query parameters that may contain secrets."""
        secret_url = "https://api.example.com/data?api_key=secret123&token=abc"
        respx_mock.get(secret_url).mock(
            return_value=httpx.Response(200, json={"result": "ok"})
        )

        from app.api import fetch_json

        with caplog.at_level(logging.DEBUG, logger="app.api"):
            await fetch_json(secret_url)

        # Only check our own log records (httpx logs the full URL internally)
        our_records = [r for r in caplog.records if r.name.startswith("app.")]
        for record in our_records:
            assert "secret123" not in record.message
            assert "api_key=secret123" not in record.message
            assert "token=abc" not in record.message
