# 2026-02-27 Session — Moonbow Lab Services MCP + Docker Sandbox Fix

## Summary

Integrated Moonbow Stack microservices (`*.frederickpi.com`) as MCP tools, fixed two critical runtime bugs (ulscar polling status mismatch, Docker sandbox cross-process reconnection), and ran LiveDRBench pilot with Qwen3-32B.

## What Was Done

### 1. Moonbow Lab Services MCP Integration

Created shared HTTP client and 5 MCP servers for Moonbow Stack services:

**Shared client** — `src/tool/mcp_servers/utils/lab_client.py`:
- `lab_request()` — async HTTP with retry + exponential backoff
- `lab_request_bytes()` — binary response variant (audio/video)
- `lab_upload()` — multipart file upload (audio STT)
- `poll_async_job()` — Celery-style single job poller (serp)
- `poll_batch_results()` — batch job poller (ulscar)

**MCP servers created**:

| Server | Config | Tools |
|--------|--------|-------|
| `lab_serp_mcp_server.py` | `tool-lab-serp.yaml` | `duckduckgo_search` |
| `lab_ulscar_mcp_server.py` | `tool-lab-ulscar.yaml` | `scrape_url`, `scrape_urls` |
| `lab_audio_mcp_server.py` | `tool-lab-audio.yaml` | `lab_audio_transcribe`, `lab_audio_translate` |
| `lab_video_mcp_server.py` | `tool-lab-video.yaml` | `get_youtube_transcript`, `download_video_audio` |
| `lab_psycholing_mcp_server.py` | `tool-lab-psycholing.yaml` | `analyze_text_psycholinguistics`, `analyze_texts_psycholinguistics` |

Design: async polling is internal to each tool call (agent doesn't manage polling). One service = one MCP server. `lab_` prefix avoids collision with existing servers.

### 2. Docker Sandbox — Dual Backend Support

Reviewed and documented existing Docker sandbox work:
- `sandbox/docker_sandbox.py` — `DockerSandbox` class (drop-in E2B replacement)
- `sandbox/Dockerfile` — Python 3.12-slim with scientific computing packages
- `python_server.py` — dual backend via `SANDBOX_BACKEND` env var (docker/e2b)

### 3. Bug Fix — ulscar Polling Status Mismatch

**Problem**: All ulscar scraping returned "Job not found in queue". Scrapes submitted OK but poller never recognized completion.

**Root cause**: `poll_batch_results()` checked `status == "completed"` but ulscar API returns `"complete"`.

**Fix** (`lab_client.py` line 217):
```python
# Before:
if status == "completed":
# After:
if status in ("complete", "completed"):
```

### 4. Bug Fix — Docker Sandbox Cross-Process Reconnection (Critical)

**Problem**: `create_sandbox` succeeded but `run_python_code` always failed with `"Failed to connect to sandbox"`. Docker containers were running fine.

**Root cause**: MCP stdio transport spawns a **fresh process per tool call**. `DockerSandbox._registry` is an in-memory dict — it gets populated during `create_sandbox` but is empty in the new process that handles `run_python_code`.

**Fix** (`sandbox/docker_sandbox.py` — `connect()` method): When `_registry` lookup fails, fall back to Docker API container lookup by name (sandbox_id == container name). If the container exists and is running, reconstruct the `DockerSandbox` object.

### 5. LiveDRBench Pilot Runs

**Config created**: `agent_livedrbench_gemini_lab.yaml`, `agent_livedrbench_qwen3_lab.yaml`

**Qwen3-32B Run 1 (before sandbox fix)** — 0/3 correct:
- Task 0: 6 turns, sandbox connect failed → empty answer
- Task 1: 5 turns, 1 scrape error → empty answer
- Task 2: 7 turns, sandbox connect failed → empty answer
- Main blocker: sandbox cross-process registry loss

**Qwen3-32B Run 2 (after sandbox fix, `max_context_length` 32768)** — 0/3 correct:
- Task 0: 20 turns, no sandbox errors, but scrape returned truncated content → `[]`
- Task 1: 3 turns, 1 scrape error, but produced names (judged incorrect) → partial answer
- Task 2: 18 turns, no sandbox errors, scrape truncated → `[]`
- Sandbox fix confirmed working (no connect failures)
- New blocker: ulscar scraping quality (see Known Issues below)

### 6. Known Issues — Ulscar Scraping

Detailed log analysis revealed two ulscar problems beyond the polling fix:

**Issue A — Truncated content on JS-rendered pages**:
- Wikipedia table pages (e.g. "List of countries by medal count at IMO") return only ~516 chars (intro paragraph + references)
- The actual data table is rendered via JavaScript; ulscar's `use_text_extraction` only captures static HTML
- The `imo-official.org/country_individual_r.aspx` pages work fine (server-side rendered)
- Task 2 msg[35]: model discovered workaround by routing through `r.jina.ai/` (Jina Reader) and got full content

**Issue B — Intermittent "Job not found in queue"**:
- Occurs under concurrent load (3 tasks × multiple scrape requests simultaneously)
- Jobs are accepted (`status: accepted`) but expire from Celery queue before results are polled
- Not a code bug — likely ulscar worker capacity issue under concurrent load
- Caused model to waste turns retrying the same URL (Task 0 used 20/20 turns mostly retrying)

**Impact**: Model enters infinite retry loops — searches for URL, scrapes, gets truncated/error, searches again. Wastes all turns without extracting useful data.

**Potential fixes**:
1. Add Jina Reader fallback in `lab_ulscar_mcp_server.py` when `text_len < threshold`
2. Increase ulscar worker pool / queue TTL on server side
3. Limit scrape retries in MCP server (return partial content instead of error)

## File Changes

### Created
- `src/tool/mcp_servers/utils/lab_client.py`
- `src/tool/mcp_servers/lab_serp_mcp_server.py`
- `src/tool/mcp_servers/lab_ulscar_mcp_server.py`
- `src/tool/mcp_servers/lab_audio_mcp_server.py`
- `src/tool/mcp_servers/lab_video_mcp_server.py`
- `src/tool/mcp_servers/lab_psycholing_mcp_server.py`
- `config/tool/tool-lab-serp.yaml`
- `config/tool/tool-lab-ulscar.yaml`
- `config/tool/tool-lab-audio.yaml`
- `config/tool/tool-lab-video.yaml`
- `config/tool/tool-lab-psycholing.yaml`
- `config/agent_livedrbench_gemini_lab.yaml`
- `config/agent_livedrbench_qwen3_lab.yaml`
- `spec/Infra/LabServices.md`

### Modified
- `sandbox/docker_sandbox.py` — cross-process reconnection fix in `connect()`
- `src/tool/mcp_servers/utils/lab_client.py` — ulscar polling status fix
- `config/agent_livedrbench_qwen3_lab.yaml` — `max_context_length` 15536 → 32768
- `spec/Infra/Tools.md` — added 5 lab tools, sandbox note
- `spec/Infra/Meta.md` — added LabServices.md routing
- `spec/Core/Technical.md` — added sandbox/ to directory tree
- `.env.template` — added `LAB_*_BASE_URL` variables

## Key Lessons

1. **MCP stdio = process-per-call**: Any state that needs to survive across tool calls must be externalized (Docker API, filesystem, etc.), not kept in memory. `DockerSandbox.connect()` now falls back to Docker API lookup by container name.
2. **API status strings**: Always verify actual API responses; don't assume `"completed"` vs `"complete"`.
3. **Scraping ≠ rendering**: `use_text_extraction` only works on static/SSR pages. JS-rendered tables (Wikipedia) need a headless browser or Jina Reader.
4. **Agent retry loops**: Without scrape quality guards, model wastes all turns retrying the same failing URL. Need server-side fallback or retry limits.

## Next Steps

- Fix ulscar scraping quality: add Jina Reader fallback for truncated results
- Address intermittent "Job not found in queue" (server-side worker capacity or queue TTL)
- Run Gemini lab benchmark for comparison (stronger model may work around scrape issues)
- Full 100-task LiveDRBench run once scraping is stable
