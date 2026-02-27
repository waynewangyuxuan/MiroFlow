# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from fastmcp import FastMCP
from src.logging.logger import setup_mcp_logging
from src.tool.mcp_servers.utils.lab_client import lab_request, poll_async_job

LAB_SERP_BASE_URL = os.environ.get(
    "LAB_SERP_BASE_URL", "https://serp.frederickpi.com"
)

setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("lab-serp-mcp-server")


def _format_search_results(results: dict) -> str:
    """Format raw search result dict into readable text."""
    if not results:
        return "No results found."

    # results may be nested: {"results": [...]} or just a dict of pages
    items = results.get("results", results)
    if isinstance(items, dict):
        # Flatten nested structure — values might be lists
        flat = []
        for v in items.values():
            if isinstance(v, list):
                flat.extend(v)
            elif isinstance(v, dict):
                flat.append(v)
        items = flat

    if not isinstance(items, list):
        return json.dumps(results, ensure_ascii=False, indent=2)

    lines = []
    for i, item in enumerate(items, 1):
        if isinstance(item, dict):
            title = item.get("title", "")
            url = item.get("href") or item.get("url") or item.get("link", "")
            snippet = item.get("body") or item.get("snippet") or item.get("description", "")
            parts = [f"{i}. {title}"]
            if url:
                parts.append(f"   URL: {url}")
            if snippet:
                parts.append(f"   {snippet}")
            lines.append("\n".join(parts))
        else:
            lines.append(f"{i}. {item}")
    return "\n\n".join(lines) if lines else "No results found."


@mcp.tool()
async def duckduckgo_search(
    query: str,
    date_range_start: str = "",
    date_range_end: str = "",
    pages: int = 1,
) -> str:
    """Search the web using DuckDuckGo. Returns organic search results
    including titles, URLs, and snippets. No daily quota limit.

    Args:
        query: The search query string.
        date_range_start: Optional start date filter (YYYY-MM-DD).
        date_range_end: Optional end date filter (YYYY-MM-DD).
        pages: Number of result pages to fetch (1-10, default: 1).

    Returns:
        Search results with titles, URLs, and snippets.
    """
    if not query or not query.strip():
        return "[ERROR]: Search query cannot be empty."

    pages = max(1, min(pages, 10))

    body: dict = {"query": query.strip(), "pages": pages}
    if date_range_start and date_range_end:
        body["date_range"] = [date_range_start, date_range_end]

    try:
        # Submit search job
        submit_resp = await lab_request(
            "POST", f"{LAB_SERP_BASE_URL}/search", json_body=body
        )
        if isinstance(submit_resp, str):
            return submit_resp  # Already an error string

        task_id = submit_resp.get("task_id")
        if not task_id:
            return f"[ERROR]: No task_id in response: {submit_resp}"

        # Poll until results are ready
        result_resp = await poll_async_job(
            status_url=f"{LAB_SERP_BASE_URL}/search/{task_id}/status",
            result_url=f"{LAB_SERP_BASE_URL}/search/{task_id}/result",
        )

        if isinstance(result_resp, str):
            return result_resp

        results = result_resp.get("results", result_resp)
        return _format_search_results(results)

    except TimeoutError:
        return "[ERROR]: Search timed out. Try a simpler query or fewer pages."
    except Exception as e:
        return f"[ERROR]: DuckDuckGo search failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
