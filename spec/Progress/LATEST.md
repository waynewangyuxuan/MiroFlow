# 2026-02-25 Session 2 — LiveDRBench Integration

## Summary

Investigated Microsoft LiveDRBench (100 deep research tasks, encrypted answers), built dashboard, created the full pipeline to run it with MiroFlow, and fixed critical bugs in `GPTOpenAIClient` that blocked Gemini from working with XML tool calls.

## What Was Done

### 1. LiveDRBench Investigation
- Found benchmark: Microsoft LiveDRBench on HuggingFace (`microsoft/LiveDRBench`)
- 100 tasks across 8 categories: entities, scifacts-geo, scifacts-materials, prior-art, novel-datasets (3 types), flights
- All tasks expect JSON output (not simple text answers)
- 91/100 answers encrypted — evaluation requires their `evaluate.py` + OpenAI judge
- Average question length: 913 chars, questions include exact JSON format specs

### 2. Dashboard (Vite + React)
- Scaffolded proper web app: Vite + React + react-router-dom + lucide-react
- Nordic minimalist design: Inter font, warm off-white bg, forest green accent, muted earth tones
- Auto-loads `data/livedrbench/raw_data.json` via Vite middleware (no manual file picking needed)
- Views: Benchmark Data (working), Trace Logs (placeholder), Experiments (placeholder)
- Design system in `src/styles/tokens.js` with documented color tokens

### 3. LiveDRBench Pipeline (Approach A — two-stage)
- **Stage 1**: MiroFlow agent runs tasks, outputs `\boxed{JSON}` answers
- **Stage 2**: Export predictions → run LiveDRBench's own `evaluate.py`

Created:
- `config/benchmark/livedrbench.yaml` — benchmark config (3 concurrent, pass@1)
- `config/agent_livedrbench_gemini_direct.yaml` — Gemini 2.5 Flash × LiveDRBench (30 turns)
- `utils/prepare_benchmark/gen_livedrbench.py` — updated: correct field names (`task_question`, `ground_truth`), preserves `key`/`canary` for eval
- `utils/livedrbench_export.py` — converter: MiroFlow results → LiveDRBench `predictions.json`

### 4. Decision: Approach A (two-stage eval)
- MiroFlow only handles agent execution (search + reason + output JSON)
- Scoring uses LiveDRBench's own eval pipeline (decrypt + LLM judge + precision/recall/F1)
- Rationale: simpler, stays compatible with their leaderboard, their eval logic may update

### 5. Critical Bug Fixes — GPTOpenAIClient + Gemini Compatibility

**Problem**: Gemini via OpenAI-compatible API uses XML `<use_mcp_tool>` tags (like Claude/DeepSeek), but `GPTOpenAIClient` only handled native OpenAI function calling. Two bugs:

**Bug 1 — Tool call parsing (`extract_tool_calls_info`)**:
- `GPTOpenAIClient` only checked `finish_reason == "tool_calls"` to detect tool use
- Gemini returns `finish_reason == "stop"` with XML tool calls in the text body
- Agent made a search call in turn 1, but orchestrator didn't see it → loop ended after 1 turn
- **Fix**: Added fallback — if `finish_reason` is not `"tool_calls"` but text contains `<use_mcp_tool>`, parse XML with `parse_llm_response_for_tool_calls()`

**Bug 2 — Tool result format (`update_message_history`)**:
- After tool execution, results were sent back as `role: "tool"` messages (OpenAI-specific format)
- Gemini's API doesn't accept `role: "tool"` messages → `BadRequestError` on turn 2
- Agent was stuck in retry loop (60s between retries, 5 attempts)
- **Fix**: Detect whether last assistant message used native `tool_calls` or XML. If XML, send tool results as `role: "user"` messages (same pattern as `ClaudeOpenRouterClient`)

**Safety**: Both fixes only trigger when native function calling is NOT used. GPT-4o/GPT-5 behavior is completely unchanged.

### 6. First Test Run (in progress)
- Running 3 tasks (`max_tasks: 3`) with Gemini 2.5 Flash
- After fixes, agent successfully executing multi-turn search loops (3-4+ turns observed)
- Results pending

## Config Changes
- Added: `config/benchmark/livedrbench.yaml`
- Added: `config/agent_livedrbench_gemini_direct.yaml`
- Added: `utils/livedrbench_export.py`
- Added: `dashboard/` (full Vite + React project)
- Added: `spec/Infra/Dashboard.md`
- Modified: `src/llm/providers/gpt_openai_client.py` (two bug fixes for XML tool call compat)
- Modified: `utils/prepare_benchmark/gen_livedrbench.py` (fixed field names)
- Modified: `spec/Infra/Benchmarks.md`, `spec/Meta.md`, `spec/Core/Technical.md`

## How to Run LiveDRBench

```bash
# 1. Re-generate standardized data (field names were fixed)
uv run python -c "from utils.prepare_benchmark.gen_livedrbench import gen_livedrbench; gen_livedrbench('data/livedrbench')"

# 2. Run agent on all 100 tasks
uv run main.py common-benchmark --config_file_name=agent_livedrbench_gemini_direct

# 3. Export predictions
uv run python utils/livedrbench_export.py \
  --results_dir logs/livedrbench/gemini_direct \
  --output predictions.json

# 4. Clone LiveDRBench repo and evaluate
git clone https://github.com/microsoft/LiveDRBench.git
cd LiveDRBench && pip install -r requirements.txt
python src/evaluate.py \
  --openai_api_key $OPENAI_API_KEY \
  --preds_file ../MiroFlow/predictions.json
```

## Next Steps
- Wait for first 3-task run to complete, inspect agent output quality
- Add trace viewer to dashboard (highest priority dashboard feature)
- Dashboard roadmap: config editor, run control, results comparison
- Try local LLM (gpt-oss-120b) on the same tasks for comparison
- Full 100-task run once output quality confirmed
