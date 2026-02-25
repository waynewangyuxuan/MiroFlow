# Technical Stack

> Tech stack, infrastructure, and configuration architecture.

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3 | Entry point: `main.py` |
| Config | Hydra + OmegaConf | YAML composition, `${oc.env:}` interpolation |
| Package Mgr | uv | Lockfile: `uv.lock`, spec: `pyproject.toml` |
| Tool Protocol | MCP (Model Context Protocol) | Each tool is a standalone MCP server |
| LLM Integration | Provider classes | Each provider implements `LLMProviderClientBase` |
| Benchmarks | Hydra defaults composition | `config/benchmark/*.yaml` |

## Three-Layer Config Model

```
Layer 1: Environment variables (.env)        — API keys, URLs
Layer 2: Declarative config (Hydra YAML)     — Model selection, tool composition
Layer 3: Runtime override (CLI args)         — Per-experiment adjustments
```

## Directory Structure

```
MiroFlow/
├── config/                  ← Hydra YAML configs
│   ├── agent_llm_*.yaml     ← LLM provider configs
│   ├── agent_{bench}_{model}.yaml  ← Experiment configs
│   ├── benchmark/*.yaml     ← Benchmark definitions
│   └── tool/*.yaml          ← MCP tool definitions
├── src/
│   ├── llm/providers/       ← LLM provider implementations
│   └── tool/mcp_servers/    ← MCP tool server implementations
├── scripts/                 ← Run scripts (multi-run, avg-score)
├── data/                    ← Benchmark datasets
├── logs/                    ← Experiment outputs (gitignored)
├── spec/                    ← Context OS spec (this directory)
└── common_benchmark.py      ← Benchmark orchestrator
```

## Config Naming Convention

Agent configs follow: `agent_{benchmark}_{model}.yaml`
- Search by benchmark: `ls config/agent_gaia-*`
- Search by model: `ls config/agent_*mirothinker*`

## Infra Details

See [Infra/Models.md](../Infra/Models.md), [Infra/Tools.md](../Infra/Tools.md), [Infra/Benchmarks.md](../Infra/Benchmarks.md).
