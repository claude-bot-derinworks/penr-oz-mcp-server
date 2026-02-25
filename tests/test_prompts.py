"""Tests for prompt templates."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.prompts import (
    summarize_text,
    extract_tasks,
    analyze_code,
    write_design_doc,
    refactor_instructions,
    summarize_prompt,
)
from server import create_mcp


# ---------------------------------------------------------------------------
# summarize_text
# ---------------------------------------------------------------------------

def test_summarize_text_prompt() -> None:
    """Test that summarize_text generates a valid prompt."""
    result = summarize_text("This is a test document.")
    assert "test document" in result
    assert "summary" in result.lower()


def test_summarize_text_includes_input() -> None:
    """Test that the user-supplied text appears verbatim in the prompt."""
    text = "Revenue grew 15% year-over-year."
    result = summarize_text(text)
    assert text in result


# ---------------------------------------------------------------------------
# extract_tasks
# ---------------------------------------------------------------------------

def test_extract_tasks_prompt() -> None:
    """Test that extract_tasks generates a valid prompt."""
    result = extract_tasks("We need to fix the login bug by Friday.")
    assert "login bug" in result
    assert "task" in result.lower()


def test_extract_tasks_includes_input() -> None:
    """Test that the user-supplied text appears verbatim in the prompt."""
    text = "Alice will update the docs; Bob will review the PR."
    result = extract_tasks(text)
    assert text in result


# ---------------------------------------------------------------------------
# analyze_code
# ---------------------------------------------------------------------------

def test_analyze_code_prompt_default_language() -> None:
    """Test that analyze_code uses python as the default language."""
    code = "def add(a, b): return a + b"
    result = analyze_code(code)
    assert code in result
    assert "python" in result.lower()


def test_analyze_code_prompt_custom_language() -> None:
    """Test that analyze_code accepts a custom language."""
    code = "int add(int a, int b) { return a + b; }"
    result = analyze_code(code, language="c")
    assert code in result
    assert "c" in result


def test_analyze_code_covers_quality_dimensions() -> None:
    """Test that the prompt asks for multiple quality dimensions."""
    result = analyze_code("x = 1")
    lower = result.lower()
    assert "quality" in lower or "readability" in lower
    assert "bug" in lower
    assert "performance" in lower
    assert "security" in lower


# ---------------------------------------------------------------------------
# write_design_doc
# ---------------------------------------------------------------------------

def test_write_design_doc_prompt() -> None:
    """Test that write_design_doc generates a valid prompt."""
    result = write_design_doc("Add caching layer")
    assert "Add caching layer" in result
    assert "design" in result.lower()


def test_write_design_doc_with_context() -> None:
    """Test that optional context is included when provided."""
    result = write_design_doc("Add caching", context="We use Redis in production.")
    assert "Add caching" in result
    assert "Redis in production" in result


def test_write_design_doc_without_context() -> None:
    """Test that the prompt is valid even without context."""
    result = write_design_doc("New auth flow")
    # Context section header should NOT appear when context is empty
    assert "Project Context" not in result


def test_write_design_doc_covers_sections() -> None:
    """Test that the prompt requests key design document sections."""
    result = write_design_doc("Search feature")
    lower = result.lower()
    assert "architecture" in lower
    assert "testing" in lower
    assert "security" in lower


# ---------------------------------------------------------------------------
# refactor_instructions
# ---------------------------------------------------------------------------

def test_refactor_instructions_prompt() -> None:
    """Test that refactor_instructions generates a valid prompt."""
    result = refactor_instructions("x = 1", issues="Too terse")
    assert "x = 1" in result
    assert "Too terse" in result


def test_refactor_instructions_custom_language() -> None:
    """Test that refactor_instructions accepts a custom language."""
    result = refactor_instructions("val x = 1", issues="Immutability", language="kotlin")
    assert "kotlin" in result


def test_refactor_instructions_covers_deliverables() -> None:
    """Test that the prompt asks for step-by-step instructions and refactored code."""
    result = refactor_instructions("a=1", issues="naming")
    lower = result.lower()
    assert "step" in lower
    assert "refactor" in lower


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

def test_summarize_prompt_backward_compatibility() -> None:
    """Test that legacy summarize_prompt still works."""
    text = "This is a test document."
    legacy_result = summarize_prompt(text)
    new_result = summarize_text(text)

    # Legacy function should produce the same output as the new one
    assert legacy_result == new_result


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_all_prompts_registered() -> None:
    """Test that all prompts including legacy are registered."""
    mcp = create_mcp()
    prompts = asyncio.run(mcp.list_prompts())

    prompt_names = list(prompts.keys()) if isinstance(prompts, dict) else [p.name for p in prompts]

    # Check new prompts are registered
    assert "summarize_text" in prompt_names
    assert "extract_tasks" in prompt_names
    assert "analyze_code" in prompt_names
    assert "write_design_doc" in prompt_names
    assert "refactor_instructions" in prompt_names

    # Check legacy prompt is also registered for backward compatibility
    assert "summarize_prompt" in prompt_names
