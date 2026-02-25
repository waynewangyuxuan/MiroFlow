# 2026-02-25 Session — Infrastructure Bootstrap

## Summary

First working session. Connected our own LLM infrastructure and verified end-to-end agent pipeline.

## What Was Done

### 1. Codebase Understanding
- Full read-through of MiroFlow architecture: Hydra config → Pipeline (ToolManager + OutputFormatter) → LLM Client → Orchestrator agent loop
- Mapped tool-calling modes: XML `<use_mcp_tool>` (Claude/DeepSeek/Qwen) vs native function calling (GPT)
- Understood MCP server protocol for tools (searching, reading, code, vision, audio, reasoning)
- Understood benchmark system: standardized JSONL format, LLM-as-Judge scoring, pass@k evaluation

### 2. New LLM Provider: Qwen3LocalClient
- Created `src/llm/providers/qwen3_local_client.py`
  - `<think>` block stripping (regex-based, handles incomplete blocks)
  - `ContextLimitError` handling for tight context windows
  - XML-based tool call parsing (reuses `parse_llm_response_for_tool_calls`)
  - Hallucinated user-content cleaning (`_clean_user_content_from_response`)
  - Text-merge message history pattern (from DeepSeek provider)

### 3. New Configs Created
- `config/agent_llm_qwen3_local.yaml` — Local LLM via `openai/gpt-oss-120b` at `localllm.frederickpi.com`
- `config/agent_llm_gemini_direct.yaml` — Gemini 2.5 Flash via Google AI API (OpenAI-compatible)
- `config/agent_llm_gemini.yaml` — Gemini via OpenRouter (using ClaudeOpenRouterClient)

### 4. Environment Setup
- Updated `.env.template` with all required keys
- User configured `.env` with: GEMINI_API_KEY, JINA_API_KEY, OPENAI_API_KEY, SERPER_API_KEY
- Dependencies installed via `uv sync` on user's machine

### 5. Bug Fixes During Testing
- Fixed Gemini model name: `gemini-2.5-flash-preview-05-20` → `gemini-2.5-flash` (old name returned 404)
- Fixed local LLM model name: `Qwen/Qwen3-32B` → `openai/gpt-oss-120b` (queried `/v1/models` endpoint to find correct name)

### 6. Verification
- Both Gemini direct and local LLM (gpt-oss-120b) configs tested successfully by user

## Config Changes
- Added: `config/agent_llm_qwen3_local.yaml`
- Added: `config/agent_llm_gemini_direct.yaml`
- Added: `config/agent_llm_gemini.yaml`
- Added: `src/llm/providers/qwen3_local_client.py`
- Modified: `.env.template`

## Next Steps
- Investigate LiveDeepResearch benchmark: find dataset format, build adapter
- Run first benchmark (e.g., GAIA-val) with Gemini direct to establish a baseline
- Test Qwen3LocalClient with more complex multi-turn tasks (context window pressure)
- Explore adding DuckDuckGo as alternative search tool
