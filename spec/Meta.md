# MiroFlow Spec

> Research agent framework — spec structure follows Research Context OS conventions.

## Routing

| Area | Path | Description |
|------|------|-------------|
| Research Objectives | [Core/Product.md](Core/Product.md) | What we're building and why |
| Technical Stack | [Core/Technical.md](Core/Technical.md) | Tech stack, infra pointers, config structure |
| Conventions | [Core/Regulation.md](Core/Regulation.md) | Code standards + experiment rules |
| LLM Providers | [Infra/Models.md](Infra/Models.md) | Available models and how to switch |
| Tool Services | [Infra/Tools.md](Infra/Tools.md) | MCP tool servers and how to add new ones |
| Benchmark Datasets | [Infra/Benchmarks.md](Infra/Benchmarks.md) | Available benchmarks and how to run them |
| Experiments | [Experiments/](Experiments/Meta.md) | Experiment designs, configs, and results |
| Decisions | [Decisions/](Decisions/Meta.md) | Architecture Decision Records |
| Progress | [Progress/](Progress/Meta.md) | Session logs with experiment context |
| Todo | [Todo.md](Todo.md) | Current task backlog |

## Config ↔ Spec Mapping

```
config/                          spec/Infra/
├── agent_llm_*.yaml       →    Models.md (provider inventory)
├── tool/*.yaml            →    Tools.md (service inventory)
├── benchmark/*.yaml       →    Benchmarks.md (dataset inventory)
└── agent_{bench}_{model}  →    Experiments/EXP-NNN/Config.md
```

## Knowledge Source

Structure derived from: Prism `research-context-os` module.
