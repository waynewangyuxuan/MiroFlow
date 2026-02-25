# MiroFlow

> Open-source research agent framework for multi-step internet research, achieving state-of-the-art benchmark performance (GAIA, HLE, BrowserComp, xBench, FutureX).

## Tech Stack

- **Language**: Python 3
- **Config**: Hydra (YAML composition with `${oc.env:}` interpolation)
- **Package Manager**: uv (lockfile: `uv.lock`)
- **Tool Protocol**: MCP servers (`src/tool/mcp_servers/`)
- **LLM Access**: Multi-provider via provider classes (`src/llm/providers/`)
- **Benchmarks**: Hydra-composed configs (`config/benchmark/`)

## Current Stage

Research — replacing infra, running benchmarks, iterating on agent performance.

## Start Working

1. Read `spec/Meta.md` — project spec routing
2. Read `spec/Core/Regulation.md` — code and experiment conventions
3. Read `spec/Experiments/Meta.md` — current experiment focus
4. Read `spec/Progress/LATEST.md` — most recent session (if exists)
