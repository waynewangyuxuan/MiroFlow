# Lab Services — Moonbow Stack

> External microservices deployed under `*.frederickpi.com`. Each service exposes `/doc` or `/docs` for auto-generated API documentation.

## Service Inventory

| Service | Endpoint | Purpose | Priority |
|---------|----------|---------|----------|
| **serp** | `serp.frederickpi.com` | DuckDuckGo async search (task queue) | Primary search |
| **google** | `google.frederickpi.com` | Google CSE search (4k/day limit) | Fallback search |
| **ulscar** | `ulscar.frederickpi.com` | Resilient web scraping + content extraction | Primary scraping |
| **localllm** | `localllm.frederickpi.com` | OpenAI-compatible LLM proxy / load balancer (vLLM) | LLM gateway |
| **audio** | `audio.frederickpi.com` | Speech AI gateway — STT, TTS, voice chat (OpenAI-compatible) | Audio processing |
| **video** | `video.frederickpi.com` | yt-dlp wrapper — media download + transcript extraction | Media acquisition |
| **proxy** | `proxy.frederickpi.com` | Rotating proxy pool (normal + Playwright formats) | Network infra |
| **psycholing** | `psycholing.frederickpi.com` | Psycholinguistic / LIWC text analysis | Text analysis |
| **gpustats** | `gpustats.frederickpi.com` | Live GPU monitoring dashboard (SSE stream) | Observability |
| **rss** | `rss.frederickpi.com` | RSS feed aggregation | Content ingestion |

## Service Details

### serp — DuckDuckGo Async Search

**Endpoint**: `https://serp.frederickpi.com`

Async job-based search service. Submit a query, get a job ID, poll for results.

- **Use case**: Web search within agent pipelines
- **Pattern**: Submit → poll status → retrieve results
- **Why async**: Multi-page and date-filtered queries can take time; don't block the caller
- **Priority**: Use this before `google` — no daily quota limit

### google — Google CSE Search

**Endpoint**: `https://google.frederickpi.com`

Google Custom Search Engine wrapper. Clean internal API for SERP results.

- **Use case**: Google-quality search when DuckDuckGo results are insufficient
- **Limit**: 4,000 requests/day — contact Frederick before heavy use
- **Priority**: Fallback only; prefer `serp` for routine searches

### ulscar — Web Scraping + Content Extraction

**Endpoint**: `https://ulscar.frederickpi.com`

Production-grade async scraping pipeline with distributed workers.

- **Use case**: URL → clean text content (for RAG, indexing, analysis)
- **Features**: Batch processing, partial failure tolerance, anti-detection
- **Pattern**: Submit URLs → async processing → best-effort extraction
- **Pipeline fit**: `serp` discovers links → `ulscar` extracts page content

### localllm — Local LLM Gateway

**Endpoint**: `https://localllm.frederickpi.com`

OpenAI-compatible proxy in front of local model backends (vLLM).

- **Use case**: Unified LLM endpoint for all internal tools
- **Features**: Load balancing, failover, automatic model discovery
- **API**: OpenAI-compatible (`/v1/chat/completions`, `/v1/models`)
- **Note**: Already integrated via `src/llm/providers/` — new LLM provider configs can point here

### audio — Speech AI Gateway (Speaches)

**Endpoint**: `https://audio.frederickpi.com`

Self-hosted voice layer with OpenAI-style endpoints.

- **STT**: Upload audio → transcription text
- **TTS**: Text → spoken audio
- **Translation**: Speech in language A → text in language B
- **Realtime**: Chat-completions-style voice interaction endpoints
- **API**: OpenAI-compatible

### video — Media Download + Transcripts

**Endpoint**: `https://video.frederickpi.com`

yt-dlp wrapper API. Returns media files directly in HTTP response (stateless).

- **Use case**: Download video/audio, extract YouTube transcripts with timestamps
- **Features**: Proxy rotation, retry logic, no server-side file storage
- **Pipeline fit**: Download media → `audio` for transcription → LLM for analysis

### proxy — Proxy Pool

**Endpoint**: `https://proxy.frederickpi.com`

Central proxy provider with rotating IPs.

- **Formats**: Normal string (HTTP clients) + Playwright-ready structure
- **Use case**: Supporting `ulscar`, browser automation, and any scraping that needs IP rotation
- **Note**: Consumed by other services internally; direct use only when needed

### psycholing — Psycholinguistic Text Analysis

**Endpoint**: `https://psycholing.frederickpi.com`

Lexicon-based text feature extraction (not LLM-based).

- **Metrics**: Emotion, concreteness, sensory language, social orientation, lexical complexity (AoA), LIWC categories
- **Use case**: Research text analysis, content comparison, writing evaluation
- **Output**: Length-normalized, interpretable numeric features

### gpustats — GPU Monitoring

**Endpoint**: `https://gpustats.frederickpi.com`

Real-time GPU utilization dashboard.

- **API**: SSE stream for live GPU metrics (utilization, memory, health)
- **Use case**: Monitor inference/training workloads

### rss — RSS Aggregation

**Endpoint**: `https://rss.frederickpi.com`

- **Status**: Currently returning 502 — service unavailable
- **Expected**: Feed ingestion, normalization, and API exposure

## Key Pipelines

These services compose into end-to-end workflows:

```
Search → Scrape → Analyze
  serp/google  →  ulscar  →  psycholing / localllm

Media → Transcribe → Analyze
  video  →  audio (STT)  →  localllm

Voice Interaction
  audio (STT)  →  localllm  →  audio (TTS)
```

## Integration Notes

- All services expose `/doc` or `/docs` — read these to auto-generate clients
- OpenAI-compatible services (`localllm`, `audio`) can reuse existing OpenAI SDK patterns
- Async services (`serp`, `ulscar`) use submit/poll pattern — need job status polling
- `proxy` service is consumed internally by other services; rarely called directly
- Base URL pattern: `https://{service}.frederickpi.com`

## Relation to Existing MCP Tools

| Lab Service | Overlaps With | Notes |
|-------------|---------------|-------|
| serp / google | `tool-searching` (Serper API) | Could replace or supplement Serper |
| ulscar | `tool-reading` (Jina), `smart_request.py` | More robust batch scraping |
| localllm | `src/llm/providers/` | Already usable as OpenAI-compatible endpoint |
| audio | `tool-audio` / `tool-audio-os` | Could back the audio MCP server |
| video | — | New capability, no current equivalent |
| psycholing | — | New capability, no current equivalent |
