# Regulation — Code & Experiment Conventions

> Append-only. New clauses must not contradict existing ones.

---

## Code Conventions

### R-CODE-001: Config changes require YAML, not code changes
When switching LLM providers or tools, create/modify YAML configs. Do not hardcode provider-specific logic in agent code.

### R-CODE-002: New LLM providers must implement LLMProviderClientBase
All provider classes live in `src/llm/providers/` and follow the existing protocol.

### R-CODE-003: New tools must be MCP servers
Tool implementations live in `src/tool/mcp_servers/` with a corresponding `config/tool/tool-*.yaml`.

### R-CODE-004: Environment variables go in .env, referenced via ${oc.env:}
Never hardcode API keys or URLs in YAML configs. Use `.env` + `${oc.env:VAR,default}`.

---

## Experiment Conventions

### R-EXP-001: Design before run
Write `Experiments/EXP-NNN/Design.md` (hypothesis + variables) before running any experiment.

### R-EXP-002: Config changes as diff
`Config.md` records only the diff from `Baselines.md`, not the full config. Any experiment can be reproduced from Baselines.md + Config.md.

### R-EXP-003: Complete results
Report all metrics, not just favorable ones. Include failure analysis.

### R-EXP-004: Multi-run for statistical validity
Use `pass_at_k` and multi-run scripts. Report average scores, not cherry-picked runs.

---

## Reproducibility Conventions

### R-REPRO-001: Config files must be committed
All YAML configs used in experiments must be version-controlled.

### R-REPRO-002: Random seeds recorded
When applicable, record random seeds in Config.md.

### R-REPRO-003: Dependencies locked
Use `uv.lock` to pin exact dependency versions. Commit the lockfile.

### R-REPRO-004: Raw results preserved
Keep original JSON results in `logs/`. Do not overwrite previous runs.
