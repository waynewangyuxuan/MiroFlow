# Progress

> Session logs with experiment context. Each session records what was done, config changes, and score deltas.

## Latest

→ [2026-02-25 — Infrastructure Bootstrap](LATEST.md)

## Session Log Template

```markdown
# YYYY-MM-DD Session

## Experiment Progress
- EXP-NNN: {description}, {benchmark} {old_score}% -> {new_score}% ({delta})
- Cause: {what changed and why}

## Config Changes
- Added/modified: {config file paths}

## Next Steps
- EXP-NNN+1: {what to try next}
```

## Archive

Older sessions move to `{YYYY-MM-DD}.md` files in this directory.
