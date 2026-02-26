"""API integration tools for external HTTP service calls."""

import asyncio
import json
import logging
import httpx
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from pydantic import ValidationError
from app.models import FetchJsonInput
from app.errors import format_validation_error

logger = logging.getLogger(__name__)

_REDACTED_URL = "<URL redacted due to error before sanitization>"


def _sanitize_url(url: str) -> str:
    """Return url with userinfo, query parameters, and fragment stripped."""
    parts = urlsplit(url)
    netloc = parts.netloc
    if '@' in netloc:
        netloc = netloc.rsplit('@', 1)[-1]
    return urlunsplit((parts.scheme, netloc, parts.path, '', ''))


class APIError(Exception):
    """Base exception for API-related errors."""
    pass


class InvalidURLError(APIError):
    """Raised when URL is invalid or malformed."""
    pass


class TimeoutError(APIError):
    """Raised when API request times out."""
    pass


class JSONDecodeError(APIError):
    """Raised when response cannot be decoded as JSON."""
    pass


class HTTPError(APIError):
    """Raised when HTTP request fails with error status."""
    pass


async def fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """
    Fetch JSON data from a public HTTP API.

    This tool demonstrates asynchronous MCP tools with proper request
    validation and error handling. It's designed as a reusable template
    for integrating with external HTTP services.

    Args:
        url: The HTTP(S) URL to fetch JSON from
        timeout: Request timeout in seconds (default: 10.0)

    Returns:
        Parsed JSON response as a dictionary

    Raises:
        InvalidURLError: If URL is malformed or uses unsupported scheme
        TimeoutError: If request exceeds timeout duration
        HTTPError: If server returns error status (4xx, 5xx)
        JSONDecodeError: If response is not valid JSON
        APIError: For other network or request errors

    Example:
        >>> await fetch_json("https://api.github.com/repos/python/cpython")
        {"name": "cpython", "full_name": "python/cpython", ...}
    """
    # Initialise safe_url to the redaction placeholder so it is always in scope
    # for all except handlers, even if sanitization fails before assignment.
    safe_url = _REDACTED_URL
    try:
        # Log invocation first so a DEBUG record is always emitted, even when
        # validation fails before safe_url can be computed.
        logger.debug("Tool invoked: fetch_json timeout=%s", timeout)

        # Validate inputs with Pydantic before using them, so type errors
        # (e.g. url=None) raise InvalidURLError rather than a generic APIError.
        validated = FetchJsonInput(url=url, timeout=timeout)
        url = validated.url
        timeout = validated.timeout

        safe_url = _sanitize_url(url)
        logger.debug("Tool fetch_json url=%r", safe_url)

        # Validate URL scheme
        if not url.startswith(("http://", "https://")):
            logger.error("Tool fetch_json invalid URL scheme: %r", safe_url)
            raise InvalidURLError(
                f"Invalid URL scheme. URL must start with http:// or https://. Got: {safe_url}"
            )

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info("Tool fetch_json succeeded: url=%r", safe_url)
            return result

    except ValidationError as e:
        msg = format_validation_error(e)
        # Try to sanitize the original url for the log; fall back to the placeholder
        # if url is not a string or urlsplit raises a ValueError (e.g. invalid IPv6).
        log_url = safe_url
        if isinstance(url, str):
            try:
                log_url = _sanitize_url(url)
            except ValueError:
                pass  # keep placeholder for unparseable URL
        logger.error("Tool fetch_json validation failed for input (url=%r, timeout=%s): %s", log_url, timeout, msg)
        raise InvalidURLError(msg) from e
    except httpx.TimeoutException as e:
        logger.error("Tool fetch_json timed out for url=%r after %s seconds", safe_url, timeout)
        raise TimeoutError(
            f"Request timed out after {timeout} seconds for URL: {safe_url}"
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error("Tool fetch_json HTTP error %s for url=%r", e.response.status_code, safe_url)
        raise HTTPError(
            f"HTTP {e.response.status_code} error for URL: {safe_url}"
        ) from e
    except httpx.InvalidURL as e:
        logger.error("Tool fetch_json invalid URL format: %r", safe_url)
        raise InvalidURLError(f"Invalid URL format: {safe_url}") from e
    except httpx.RequestError as e:
        logger.error("Tool fetch_json network error for url=%r", safe_url, exc_info=True)
        raise APIError(
            f"Network error occurred while fetching {safe_url}"
        ) from e
    except json.JSONDecodeError as e:
        logger.error("Tool fetch_json JSON decode error for url=%r", safe_url, exc_info=True)
        raise JSONDecodeError(
            f"Failed to decode JSON response from {safe_url}. "
            f"Response may not be valid JSON."
        ) from e
    except APIError:
        # Re-raise our custom exceptions without wrapping
        raise
    except asyncio.CancelledError:
        # Re-raise cancellation to allow proper task cleanup
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error("Tool fetch_json unexpected error for url=%r", safe_url, exc_info=True)
        raise APIError(f"Unexpected error fetching {safe_url}") from e
