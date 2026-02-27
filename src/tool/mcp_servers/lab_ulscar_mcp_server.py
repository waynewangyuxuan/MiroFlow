# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import os
from fastmcp import FastMCP
from src.logging.logger import setup_mcp_logging
from src.tool.mcp_servers.utils.lab_client import lab_request, poll_batch_results

LAB_ULSCAR_BASE_URL = os.environ.get(
    "LAB_ULSCAR_BASE_URL", "https://ulscar.frederickpi.com"
)

setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("lab-ulscar-mcp-server")


def _format_scrape_results(resp: dict) -> str:
    """Format batch scrape results into readable text."""
    results = resp.get("results", [])
    if not results:
        return "No results returned."

    parts = []
    for r in results:
        url = r.get("url", "unknown")
        if r.get("success") and r.get("text"):
            text = r["text"]
            parts.append(f"=== {url} ===\n{text}")
        else:
            error = r.get("error", "Unknown error")
            parts.append(f"=== {url} ===\n[FAILED]: {error}")

    progress = resp.get("progress", "")
    header = f"Scrape progress: {progress}\n\n" if progress else ""
    return header + "\n\n".join(parts)


@mcp.tool()
async def scrape_url(url: str) -> str:
    """Scrape a single web page and extract its text content.
    Uses distributed processing with proxy rotation and retry for resilience.

    Args:
        url: The URL to scrape.

    Returns:
        The extracted text content of the page.
    """
    if not url or not url.strip():
        return "[ERROR]: URL cannot be empty."

    try:
        # Submit single URL as batch
        body = {
            "urls": [url.strip()],
            "use_text_extraction": True,
            "use_bypass_paywall": True,
            "use_wbm": True,
            "headless": True,
            "processes": 8,
        }
        submit_resp = await lab_request(
            "POST", f"{LAB_ULSCAR_BASE_URL}/scrape", json_body=body
        )
        if isinstance(submit_resp, str):
            return submit_resp

        job_ids = submit_resp.get("job_ids", [])
        if not job_ids:
            return f"[ERROR]: No job_ids in response: {submit_resp}"

        # Poll for results
        result_resp = await poll_batch_results(
            results_url=f"{LAB_ULSCAR_BASE_URL}/results_batch",
            job_ids=job_ids,
        )
        if isinstance(result_resp, str):
            return result_resp

        # Extract the single result
        results = result_resp.get("results", [])
        for r in results:
            if r.get("success") and r.get("text"):
                return r["text"]
            elif r.get("error"):
                return f"[ERROR]: Scraping failed for {url}: {r['error']}"

        return f"[ERROR]: No content extracted from {url}."

    except TimeoutError:
        return f"[ERROR]: Scraping timed out for {url}."
    except Exception as e:
        return f"[ERROR]: Scraping failed: {e}"


@mcp.tool()
async def scrape_urls(urls: list[str]) -> str:
    """Scrape multiple web pages and extract their text content in a single batch.
    Uses distributed processing with proxy rotation. Partial failures are
    tolerated — successful results are returned even if some URLs fail.

    Args:
        urls: List of URLs to scrape (1 or more).

    Returns:
        Extracted text content for each URL, or error details for failed URLs.
    """
    if not urls:
        return "[ERROR]: URL list cannot be empty."

    cleaned = [u.strip() for u in urls if u and u.strip()]
    if not cleaned:
        return "[ERROR]: No valid URLs provided."

    try:
        body = {
            "urls": cleaned,
            "use_text_extraction": True,
            "use_bypass_paywall": True,
            "use_wbm": True,
            "headless": True,
            "processes": 8,
        }
        submit_resp = await lab_request(
            "POST", f"{LAB_ULSCAR_BASE_URL}/scrape", json_body=body
        )
        if isinstance(submit_resp, str):
            return submit_resp

        job_ids = submit_resp.get("job_ids", [])
        if not job_ids:
            return f"[ERROR]: No job_ids in response: {submit_resp}"

        result_resp = await poll_batch_results(
            results_url=f"{LAB_ULSCAR_BASE_URL}/results_batch",
            job_ids=job_ids,
        )
        if isinstance(result_resp, str):
            return result_resp

        return _format_scrape_results(result_resp)

    except TimeoutError:
        return "[ERROR]: Batch scraping timed out. Try fewer URLs."
    except Exception as e:
        return f"[ERROR]: Batch scraping failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
