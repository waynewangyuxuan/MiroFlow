# Baselines

> Reference scores and default configurations. All experiments record their Config.md as a diff from these baselines.

## Baseline Scores (MiroFlow v0.3)

| Benchmark | Model | Score | Config |
|-----------|-------|-------|--------|
| GAIA Validation | Claude 3.7 Sonnet | 73.94% pass@1 | `agent_gaia-validation_claude37sonnet.yaml` |
| HLE | Claude 3.7 Sonnet | 27.2% | `agent_hle_claude37sonnet.yaml` |
| HLE Text-Only | Claude 3.7 Sonnet | 29.5% | `agent_hle-text-only_claude37sonnet.yaml` |
| BrowserComp EN | Claude 3.7 Sonnet | 33.2% | `agent_browsecomp-en_claude37sonnet.yaml` |
| BrowserComp ZH | Claude 3.7 Sonnet | 47.1% | `agent_browsecomp-zh_claude37sonnet.yaml` |
| xBench-DS | Claude 3.7 Sonnet | 72.0% | `agent_xbench-ds_claude37sonnet.yaml` |
| FutureX | GPT-5 | #1 ranking | `agent_gaia-validation-gpt5.yaml` |

## Default Configuration (Baseline)

The baseline configuration for experiments is Claude 3.7 Sonnet via OpenRouter:

| Parameter | Value |
|-----------|-------|
| Provider | `ClaudeOpenRouterClient` |
| Model | `anthropic/claude-3.7-sonnet` |
| Temperature | 0.3 |
| Max Tokens | 32000 |
| Tools | `tool-reading`, `tool-searching` |
| Max Turns | 20 |
| Max Tool Calls/Turn | 10 |

## Design.md Template

```markdown
# EXP-NNN: {Title}
**Hypothesis**: {Changing X will lead to Y}
**Independent Variable**: {What changes}
**Control Variable**: Reference Baselines.md
**Dependent Variable**: {What to measure}
**Dataset**: {Which benchmark}
**Expected Outcome**: {Direction + magnitude}
```
