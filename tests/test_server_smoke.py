"""Smoke tests for server scaffolding."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import create_mcp


def test_server_registers_components() -> None:
    """Server initializes with at least one tool, resource, and prompt."""
    mcp = create_mcp()

    tools = asyncio.run(mcp.list_tools())
    resources = asyncio.run(mcp.list_resources())
    prompts = asyncio.run(mcp.list_prompts())

    assert tools, "Expected at least one registered tool."
    assert resources, "Expected at least one registered resource."
    assert prompts, "Expected at least one registered prompt."
