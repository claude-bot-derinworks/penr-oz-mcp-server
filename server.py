"""MCP server entrypoint for penr-oz."""

import logging

from fastmcp import FastMCP

from app.api import fetch_json
from app.config import SERVER_NAME, setup_logging
from app.prompts import (
    summarize_text,
    extract_tasks,
    analyze_code,
    write_design_doc,
    refactor_instructions,
    summarize_prompt,  # Legacy alias for backward compatibility
)
from app.resources import info, ozfs_resource
from app.tools import ping, list_files, read_text_file

logger = logging.getLogger(__name__)


def create_mcp() -> FastMCP:
    """Create and configure the FastMCP server instance."""
    mcp = FastMCP(name=SERVER_NAME)

    # Register tools
    mcp.tool(ping)
    mcp.tool(list_files)
    mcp.tool(read_text_file)
    mcp.tool(fetch_json)

    # Register resources
    mcp.resource("oz://info")(info)
    mcp.resource("ozfs://{path}")(ozfs_resource)

    # Register prompts
    mcp.prompt(summarize_text)
    mcp.prompt(extract_tasks)
    mcp.prompt(analyze_code)
    mcp.prompt(write_design_doc)
    mcp.prompt(refactor_instructions)

    # Legacy prompts (for backward compatibility)
    mcp.prompt(summarize_prompt)

    return mcp


def main() -> None:
    """Run the MCP server."""
    setup_logging()
    logger.info("Starting %s", SERVER_NAME)
    mcp = create_mcp()
    logger.info("Server configured — tools, resources, and prompts registered")
    mcp.run()


if __name__ == "__main__":
    main()
