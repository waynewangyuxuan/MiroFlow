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
