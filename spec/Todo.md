# Todo

> Current task backlog for the project.

## Active

| Priority | Task | Related EXP | Notes |
|----------|------|-------------|-------|
| P0 | Full 100-task LiveDRBench run (Gemini 2.5 Flash) | EXP-001 | Awaiting 3-task pilot results; then scale to 100 |
| P0 | Inspect 3-task pilot output quality | EXP-001 | Check traces, verify tool usage + answer extraction |
| P1 | Run LiveDRBench with gpt-oss-120b | — | Compare local LLM vs Gemini on same tasks |
| P1 | Dashboard: results/comparison view | — | Side-by-side model comparison on LiveDRBench |
| P2 | Dashboard: config editor + run control | — | Launch benchmark runs from dashboard UI |
| P2 | Add DuckDuckGo as alternative search tool | — | Reduce Serper dependency |
| P2 | Run GAIA-val baseline with Gemini direct | — | Secondary benchmark, lower priority than LiveDRBench |

## Completed

| Task | Date | Notes |
|------|------|-------|
| Initialize Context OS structure | 2026-02-24 | Applied research-context-os module |
| Bootstrap LLM infra (Gemini + local) | 2026-02-25 | 3 configs, 1 new provider, all verified |
| Investigate LiveDRBench benchmark | 2026-02-25 | 100 tasks, 8 categories, encrypted answers, HF dataset downloaded |
| Build LiveDRBench pipeline (download → run → export → eval) | 2026-02-25 | gen_livedrbench.py, benchmark config, agent config, export script |
| Fix GPTOpenAIClient XML tool-call support | 2026-02-25 | Two bugs: extract_tool_calls_info + update_message_history |
| Build incremental dashboard (Vite + React) | 2026-02-25 | Nordic minimalist design, auto-loads data, task explorer |
| Launch 3-task LiveDRBench pilot run | 2026-02-25 | Agent successfully multi-turn searching after fixes |
| Dashboard: trace viewer | 2026-02-27 | TraceOverview + MessageTimeline + useTraceLoader, recharts analytics |
