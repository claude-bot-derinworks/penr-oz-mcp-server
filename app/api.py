"""API integration tools for external HTTP service calls."""

import asyncio
import logging
import httpx
from typing import Any
from pydantic import ValidationError
from app.models import FetchJsonInput
from app.errors import format_validation_error

logger = logging.getLogger(__name__)


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
    # Strip query parameters from URL before logging to avoid leaking
    # sensitive values that may appear as query parameters (API keys, tokens).
    safe_url = url.split("?")[0]
    logger.debug("Tool invoked: fetch_json url=%r timeout=%s", safe_url, timeout)

    # Validate inputs with Pydantic
    try:
        validated = FetchJsonInput(url=url, timeout=timeout)
    except ValidationError as e:
        msg = format_validation_error(e)
        logger.error("Tool fetch_json validation failed: %s", msg)
        raise InvalidURLError(msg) from e

    url = validated.url
    timeout = validated.timeout

    # Validate URL scheme
    if not url.startswith(("http://", "https://")):
        logger.error("Tool fetch_json invalid URL scheme: %r", safe_url)
        raise InvalidURLError(
            f"Invalid URL scheme. URL must start with http:// or https://. Got: {url}"
        )

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.TimeoutException as e:
                logger.error("Tool fetch_json timed out after %s seconds", timeout)
                raise TimeoutError(
                    f"Request timed out after {timeout} seconds for URL: {url}"
                ) from e
            except httpx.HTTPStatusError as e:
                logger.error("Tool fetch_json HTTP error %s for url=%r", e.response.status_code, safe_url)
                raise HTTPError(
                    f"HTTP {e.response.status_code} error for URL: {url}"
                ) from e
            except httpx.InvalidURL as e:
                logger.error("Tool fetch_json invalid URL format: %r", safe_url)
                raise InvalidURLError(f"Invalid URL format: {url}") from e
            except httpx.RequestError as e:
                logger.error("Tool fetch_json network error for url=%r: %s", safe_url, e)
                raise APIError(
                    f"Network error occurred while fetching {url}: {str(e)}"
                ) from e

            # Parse JSON response
            try:
                result = response.json()
                logger.info("Tool fetch_json succeeded: url=%r", safe_url)
                return result
            except Exception as e:
                logger.error("Tool fetch_json JSON decode error for url=%r", safe_url)
                raise JSONDecodeError(
                    f"Failed to decode JSON response from {url}. "
                    f"Response may not be valid JSON."
                ) from e

    except APIError:
        # Re-raise our custom exceptions
        raise
    except asyncio.CancelledError:
        # Re-raise cancellation to allow proper task cleanup
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error("Tool fetch_json unexpected error for url=%r: %s", safe_url, e)
        raise APIError(f"Unexpected error fetching {url}: {str(e)}") from e
