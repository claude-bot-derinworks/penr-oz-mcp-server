"""Centralized validation error handling for MCP tools and resources."""

from pydantic import ValidationError


class ValidationErrorDetail:
    """Structured representation of a single validation error."""

    def __init__(self, field: str, message: str, value: object = None):
        self.field = field
        self.message = message
        self.value = value

    def to_dict(self) -> dict:
        result = {"field": self.field, "message": self.message}
        if self.value is not None:
            result["value"] = self.value
        return result


def format_validation_error(exc: ValidationError) -> str:
    """Format a Pydantic ValidationError into a human-readable string.

    Args:
        exc: The Pydantic ValidationError to format

    Returns:
        A structured, human-readable error message
    """
    details = extract_error_details(exc)
    parts = [f"Validation error: {len(details)} issue(s) found"]
    for detail in details:
        parts.append(f"  - {detail.field}: {detail.message}")
    return "\n".join(parts)


def extract_error_details(exc: ValidationError) -> list[ValidationErrorDetail]:
    """Extract structured error details from a Pydantic ValidationError.

    Args:
        exc: The Pydantic ValidationError to extract from

    Returns:
        List of ValidationErrorDetail objects
    """
    details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"]) or "input"
        message = error["msg"]
        value = error.get("input")
        details.append(ValidationErrorDetail(field=field, message=message, value=value))
    return details
