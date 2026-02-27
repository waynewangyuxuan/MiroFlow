# Tools — MCP Service Inventory

> All available tool servers. Each tool is a standalone MCP server defined in `config/tool/`.

## Available Tools

| Tool | Config File | Implementation | Purpose |
|------|------------|----------------|---------|
| Searching | `tool-searching.yaml` | `src.tool.mcp_servers.searching_mcp_server` | Web search via Serper + page reading via Jina |
| Searching (Serper npx) | `tool-searching-serper.yaml` | `serper-search-scrape-mcp-server` (npx) | Serper's official MCP server |
| Reading | `tool-reading.yaml` | `src.tool.mcp_servers.reading_mcp_server` | Web page reading |
| Browsing | `tool-browsing.yaml` | `src.tool.mcp_servers.browsing_mcp_server` | AI-powered web browsing (Claude/GPT) |
| Code Execution | `tool-code.yaml` | `src.tool.mcp_servers.python_server` | Python code execution via E2B |
| Reasoning | `tool-reasoning.yaml` | `src.tool.mcp_servers.reasoning_mcp_server` | Extended thinking (Claude/OpenAI) |
| Reasoning OS | `tool-reasoning-os.yaml` | — | OS-variant of reasoning |
| Audio | `tool-audio.yaml` | — | Audio processing |
| Audio OS | `tool-audio-os.yaml` | — | OS-variant of audio |
| Image/Video | `tool-image-video.yaml` | — | Image and video processing |
| Image/Video OS | `tool-image-video-os.yaml` | — | OS-variant of image/video |
| MarkItDown | `tool-markitdown.yaml` | — | Document conversion |
| Lab Search (DDG) | `tool-lab-serp.yaml` | `src.tool.mcp_servers.lab_serp_mcp_server` | DuckDuckGo search via Moonbow serp service |
| Lab Scraping | `tool-lab-ulscar.yaml` | `src.tool.mcp_servers.lab_ulscar_mcp_server` | Resilient web scraping via Moonbow ulscar |
| Lab Audio | `tool-lab-audio.yaml` | `src.tool.mcp_servers.lab_audio_mcp_server` | Speech-to-text via Moonbow Speaches (Whisper) |
| Lab Video | `tool-lab-video.yaml` | `src.tool.mcp_servers.lab_video_mcp_server` | Video download & transcripts via Moonbow yt-dlp |
| Lab Psycholing | `tool-lab-psycholing.yaml` | `src.tool.mcp_servers.lab_psycholing_mcp_server` | Psycholinguistic text analysis |

## How Tools Are Used

Agent configs select tools via `tool_config` list:

```yaml
main_agent:
  tool_config:
    - tool-reading
    - tool-searching      # swap to tool-searching-serper for alternative
```

## How to Add a New Tool

1. Create MCP server in `src/tool/mcp_servers/{name}_mcp_server.py`
2. Create `config/tool/tool-{name}.yaml`:
   ```yaml
   name: "tool-{name}"
   tool_command: "python"
   args: ["-m", "src.tool.mcp_servers.{name}_mcp_server"]
   env:
     API_KEY: "${oc.env:YOUR_API_KEY}"
   ```
3. Add API key to `.env.template` and `.env`
4. Reference in agent config's `tool_config` list
5. Update this document

## Environment Variables

| Variable | Used By |
|----------|---------|
| `SERPER_API_KEY` | tool-searching, tool-searching-serper |
| `JINA_API_KEY` | tool-searching, tool-reading |
| `E2B_API_KEY` | tool-code |
| `ANTHROPIC_API_KEY` | tool-browsing, tool-reasoning |
| `OPENAI_API_KEY` | tool-browsing, tool-reasoning |
| `LAB_SERP_BASE_URL` | tool-lab-serp (default: `https://serp.frederickpi.com`) |
| `LAB_ULSCAR_BASE_URL` | tool-lab-ulscar (default: `https://ulscar.frederickpi.com`) |
| `LAB_AUDIO_BASE_URL` | tool-lab-audio (default: `https://audio.frederickpi.com`) |
| `LAB_AUDIO_MODEL` | tool-lab-audio (default: `Systran/faster-whisper-base`) |
| `LAB_VIDEO_BASE_URL` | tool-lab-video (default: `https://video.frederickpi.com`) |
| `LAB_PSYCHOLING_BASE_URL` | tool-lab-psycholing (default: `https://psycholing.frederickpi.com`) |
