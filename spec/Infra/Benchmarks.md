# Benchmarks — Dataset Inventory

> All available benchmark datasets. Each benchmark is a Hydra config in `config/benchmark/`.

## Available Benchmarks

| Benchmark | Config File | Description | Concurrency | Pass@K |
|-----------|------------|-------------|-------------|--------|
| Default | `default.yaml` | Base config (inherited by others) | 5 | 1 |
| GAIA Validation | `gaia-validation.yaml` | General AI assistant tasks | 10 | 1 |
| GAIA Validation (text-only) | `gaia-validation-text-only.yaml` | GAIA without multimodal | — | — |
| GAIA Test | `gaia-test.yaml` | GAIA test split | — | — |
| HLE | `hle.yaml` | Hard-level evaluation | — | — |
| HLE (text-only) | `hle-text-only.yaml` | HLE without multimodal | — | — |
| BrowserComp EN | `browsecomp-en.yaml` | Web browsing (English) | — | — |
| BrowserComp ZH | `browsecomp-zh.yaml` | Web browsing (Chinese) | — | — |
| xBench-DS | `xbench-ds.yaml` | Deep search benchmark | — | — |
| FutureX | `futurex.yaml` | Future event prediction | — | — |
| WebWalkerQA | `webwalkerqa.yaml` | Web walking QA | — | — |
| FinSearchComp | `finsearchcomp.yaml` | Financial search | — | — |
| Example Dataset | `example_dataset.yaml` | Quick-start example | — | — |
| **LiveDRBench** | `livedrbench.yaml` (pending) | Microsoft deep research claim discovery (100 tasks, encrypted answers) | — | — |

## How to Run a Benchmark

```bash
# Single run
uv run main.py common-benchmark --config_file_name=agent_gaia-validation_claude37sonnet

# Multi-run (statistical validity)
for i in $(seq 1 $NUM_RUNS); do
    uv run main.py common-benchmark \
        --config_file_name=$CONFIG \
        output_dir="$DIR/run_$i"
done
uv run main.py avg-score "$DIR"
```

## Results Storage

```
logs/{benchmark}/{config}_{timestamp}/
  run_N/
    .hydra/           <- Full merged config snapshot (auto-generated)
    task_logs/        <- Per-task conversation history
    results.json      <- Aggregated results
    accuracy.txt      <- Final score
```

## How to Add a New Benchmark

1. Prepare dataset in `data/{benchmark-name}/` with `standardized_data.jsonl`
2. Create `config/benchmark/{name}.yaml`:
   ```yaml
   defaults:
     - default
     - _self_
   name: "{name}"
   data:
     data_dir: "${data_dir}/{name}"
   execution:
     max_concurrent: 10
     pass_at_k: 1
   ```
3. Create agent config: `config/agent_{name}_{model}.yaml`
4. Update this document
