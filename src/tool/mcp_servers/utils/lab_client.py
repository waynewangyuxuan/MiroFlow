# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

"""Shared async HTTP client for Moonbow Lab Services (*.frederickpi.com).

Provides:
- lab_request / lab_request_bytes: async HTTP with retry + exponential backoff
- lab_upload: multipart file upload
- poll_async_job: generic Celery-style job poller (serp, ulscar)
"""

import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300  # 5 min per request
DEFAULT_MAX_RETRIES = 3
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_POLL_MAX_WAIT = 600  # 10 min total polling


async def lab_request(
    method: str,
    url: str,
    *,
    json_body: dict | None = None,
    data: str | bytes | None = None,
    params: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict | str:
    """Make an async HTTP request to a lab service with retry logic.

    Returns parsed JSON dict on success, or raises on final failure.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=json_body,
                    data=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    text = await resp.text()
                    if resp.status >= 500:
                        raise aiohttp.ServerConnectionError(
                            f"Server error {resp.status}: {text[:500]}"
                        )
                    if resp.status >= 400:
                        return f"[ERROR]: HTTP {resp.status} from {url}: {text[:500]}"
                    try:
                        return await resp.json(content_type=None)
                    except Exception:
                        return text
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = min(2 ** (attempt + 1), 30)
                logger.warning(
                    "lab_request %s %s attempt %d failed: %s  (retry in %ds)",
                    method, url, attempt + 1, e, wait,
                )
                await asyncio.sleep(wait)
    raise last_error  # type: ignore[misc]


async def lab_request_bytes(
    method: str,
    url: str,
    *,
    json_body: dict | None = None,
    params: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> tuple[bytes, str]:
    """Like lab_request but returns (raw_bytes, content_type)."""
    last_error = None
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=json_body,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status >= 400:
                        text = await resp.text()
                        raise aiohttp.ClientResponseError(
                            resp.request_info,
                            resp.history,
                            status=resp.status,
                            message=text[:500],
                        )
                    content_type = resp.content_type or ""
                    body = await resp.read()
                    return body, content_type
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(min(2 ** (attempt + 1), 30))
    raise last_error  # type: ignore[misc]


async def lab_upload(
    url: str,
    *,
    file_path: str | None = None,
    file_bytes: bytes | None = None,
    file_name: str = "file",
    field_name: str = "file",
    extra_fields: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict | str:
    """Upload a file via multipart form to a lab service endpoint."""
    last_error = None
    for attempt in range(max_retries):
        try:
            form = aiohttp.FormData()
            if file_path:
                form.add_field(field_name, open(file_path, "rb"), filename=file_name)
            elif file_bytes:
                form.add_field(field_name, file_bytes, filename=file_name)
            else:
                raise ValueError("Either file_path or file_bytes must be provided")
            if extra_fields:
                for k, v in extra_fields.items():
                    form.add_field(k, str(v))
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        return f"[ERROR]: HTTP {resp.status} from {url}: {text[:500]}"
                    try:
                        return await resp.json(content_type=None)
                    except Exception:
                        return text
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(min(2 ** (attempt + 1), 30))
    raise last_error  # type: ignore[misc]


async def poll_async_job(
    status_url: str,
    result_url: str,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_wait: float = DEFAULT_POLL_MAX_WAIT,
) -> dict:
    """Generic poller for Celery-style async jobs.

    Polls status_url until SUCCESS/FAILURE, then fetches result_url.
    Returns parsed JSON result dict.
    """
    elapsed = 0.0
    interval = poll_interval
    while elapsed < max_wait:
        resp = await lab_request("GET", status_url, max_retries=1)
        if isinstance(resp, str):
            # Error string — wait and retry
            await asyncio.sleep(interval)
            elapsed += interval
            continue
        status = resp.get("status", "").upper()
        if status == "SUCCESS":
            return await lab_request("GET", result_url)
        if status in ("FAILURE", "REVOKED"):
            error = resp.get("error") or resp.get("message") or "Unknown error"
            raise RuntimeError(f"Job failed: {error}")
        # PENDING / STARTED / PROGRESS — keep polling
        await asyncio.sleep(interval)
        elapsed += interval
        # Adaptive: slow down after 20s
        if elapsed > 20 and interval < 5:
            interval = 5.0
    raise TimeoutError(f"Job polling timed out after {max_wait}s (last status: {resp})")


async def poll_batch_results(
    results_url: str,
    job_ids: list[str],
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_wait: float = DEFAULT_POLL_MAX_WAIT,
) -> dict:
    """Poll for batch job results (ulscar pattern).

    POSTs job_ids to results_url. Returns when all complete or max_wait exceeded.
    """
    elapsed = 0.0
    interval = poll_interval
    last_resp: dict = {}
    while elapsed < max_wait:
        resp = await lab_request("POST", results_url, json_body=job_ids)
        if isinstance(resp, str):
            await asyncio.sleep(interval)
            elapsed += interval
            continue
        last_resp = resp
        status = resp.get("status", "").lower()
        if status in ("complete", "completed"):
            return resp
        # Still processing — keep polling
        await asyncio.sleep(interval)
        elapsed += interval
        if elapsed > 20 and interval < 5:
            interval = 5.0
    # Return partial results if available
    if last_resp:
        return last_resp
    raise TimeoutError(f"Batch polling timed out after {max_wait}s")
