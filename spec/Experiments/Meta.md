# Experiments

> Experiment tracking — each experiment gets its own `EXP-NNN/` folder.

## Current Focus

No experiments started yet. See [Baselines.md](Baselines.md) for reference scores.

## Experiment Index

| ID | Title | Status | Benchmark | Key Result |
|----|-------|--------|-----------|------------|
| — | — | — | — | — |

## Experiment Structure

Each experiment folder follows this template:

```
EXP-NNN/
├── Design.md      <- Hypothesis + variables + dataset + expected outcome
├── Config.md      <- Diff from Baselines.md (not full config)
└── Results.md     <- Metrics + analysis + conclusion + next steps
```

## How to Start a New Experiment

1. Create `spec/Experiments/EXP-NNN/` folder
2. Write `Design.md` first (see template in [Baselines.md](Baselines.md))
3. Create corresponding `config/agent_{benchmark}_{model}.yaml`
4. Record config diff in `Config.md`
5. Run benchmark, fill in `Results.md`
6. Update this index table
