# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

"""Web page reader via Jina AI Reader + Moonbow proxy pool.

Uses r.jina.ai to convert any URL to clean Markdown (handles JS-rendered pages),
routed through proxy.frederickpi.com for high throughput (~1620 RPM across pool).
"""

import asyncio
import logging
import os

import aiohttp
from fastmcp import FastMCP
from src.logging.logger import setup_mcp_logging

LAB_PROXY_BASE_URL = os.environ.get(
    "LAB_PROXY_BASE_URL", "https://proxy.frederickpi.com"
)
JINA_READER_BASE_URL = os.environ.get(
    "JINA_READER_BASE_URL", "https://r.jina.ai"
)
# Max content length to return (avoid flooding LLM context)
MAX_CONTENT_LENGTH = int(os.environ.get("LAB_READER_MAX_CONTENT", "50000"))

logger = logging.getLogger(__name__)
setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("lab-reader-mcp-server")


async def _get_proxy() -> str | None:
    """Fetch a random proxy from the pool. Returns proxy URL or None."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{LAB_PROXY_BASE_URL}/proxy/random/normal",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                proxy_str = data.get("proxy", "")
                if not proxy_str:
                    return None
                # Format: ip:port:user:pass → http://user:pass@ip:port
                parts = proxy_str.split(":")
                if len(parts) == 4:
                    return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                return None
    except Exception as e:
        logger.warning("Failed to get proxy: %s", e)
        return None


async def _jina_fetch(url: str, proxy: str | None = None, timeout: int = 30) -> str:
    """Fetch a URL via Jina Reader, optionally through a proxy."""
    jina_url = f"{JINA_READER_BASE_URL}/{url}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            jina_url,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers={"Accept": "text/plain"},
        ) as resp:
            if resp.status == 429:
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history,
                    status=429, message="Rate limited",
                )
            if resp.status >= 400:
                text = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history,
                    status=resp.status, message=text[:300],
                )
            return await resp.text()


@mcp.tool()
async def read_url(url: str) -> str:
    """Read a web page and extract its content as clean Markdown text.
    Handles JavaScript-rendered pages, dynamic tables, and complex layouts.
    Uses Jina AI Reader with proxy rotation for high reliability.

    Args:
        url: The URL to read.

    Returns:
        The page content as clean Markdown text, suitable for LLM processing.
    """
    if not url or not url.strip():
        return "[ERROR]: URL cannot be empty."

    url = url.strip()
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            proxy = await _get_proxy()
            text = await _jina_fetch(url, proxy=proxy)

            if not text or len(text.strip()) < 50:
                # Very short response — might be blocked, retry with different proxy
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return f"[ERROR]: Page returned very little content ({len(text)} chars)."

            # Truncate if too long
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH] + f"\n\n[TRUNCATED at {MAX_CONTENT_LENGTH} chars]"

            return text

        except aiohttp.ClientResponseError as e:
            last_error = e
            if e.status == 429 and attempt < max_retries - 1:
                # Rate limited — retry with a different proxy
                await asyncio.sleep(2)
                continue
            return f"[ERROR]: HTTP {e.status} reading {url}: {e.message}"
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue

    return f"[ERROR]: Failed to read {url} after {max_retries} attempts: {last_error}"


@mcp.tool()
async def read_urls(urls: list[str]) -> str:
    """Read multiple web pages and extract their content as clean Markdown.
    Pages are fetched concurrently through different proxies for speed.
    Partial failures are tolerated — successful results are returned even
    if some URLs fail.

    Args:
        urls: List of URLs to read (1 or more, max 10).

    Returns:
        Extracted Markdown content for each URL, or error details for failures.
    """
    if not urls:
        return "[ERROR]: URL list cannot be empty."

    cleaned = [u.strip() for u in urls if u and u.strip()]
    if not cleaned:
        return "[ERROR]: No valid URLs provided."

    if len(cleaned) > 10:
        cleaned = cleaned[:10]

    async def _fetch_one(u: str) -> tuple[str, str]:
        """Returns (url, content_or_error)."""
        try:
            proxy = await _get_proxy()
            text = await _jina_fetch(u, proxy=proxy, timeout=45)
            if not text or len(text.strip()) < 50:
                return u, "[FAILED]: Very little content returned."
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH] + f"\n\n[TRUNCATED at {MAX_CONTENT_LENGTH} chars]"
            return u, text
        except Exception as e:
            return u, f"[FAILED]: {e}"

    results = await asyncio.gather(*[_fetch_one(u) for u in cleaned])

    parts = []
    for url_result, content in results:
        parts.append(f"=== {url_result} ===\n{content}")

    return "\n\n".join(parts)


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
