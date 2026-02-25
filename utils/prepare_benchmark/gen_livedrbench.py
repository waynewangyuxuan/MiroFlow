# SPDX-FileCopyrightText: 2026
#
# SPDX-License-Identifier: Apache-2.0

"""
Download and prepare Microsoft LiveDRBench dataset.

Usage (from project root):
    uv run python -c "from utils.prepare_benchmark.gen_livedrbench import gen_livedrbench; gen_livedrbench('data/livedrbench')"

Or via the prepare-benchmark CLI once integrated:
    uv run main.py prepare-benchmark get livedrbench
"""

import json
import pathlib


def gen_livedrbench(output_dir: str):
    """Download LiveDRBench from HuggingFace and convert to standardized format."""
    from datasets import load_dataset

    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Download from HuggingFace
    print("Downloading microsoft/LiveDRBench v1-full...")
    ds = load_dataset("microsoft/LiveDRBench", "v1-full", split="test")
    print(f"Downloaded {len(ds)} tasks")

    # Save raw data for dashboard inspection
    raw_data = [dict(row) for row in ds]
    raw_path = output_path / "raw_data.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)
    print(f"Saved raw data to {raw_path}")

    # Convert to MiroFlow standardized_data.jsonl format
    # Field names must match what common_benchmark.entrypoint() expects:
    #   task_id, task_question, ground_truth, metadata
    # LiveDRBench answers are encrypted — evaluation is done externally.
    standardized_path = output_path / "standardized_data.jsonl"
    with open(standardized_path, "w", encoding="utf-8") as f:
        for i, row in enumerate(raw_data):
            entry = {
                "task_id": f"livedrbench_{i}",
                "task_question": row.get("question", ""),
                "ground_truth": "__ENCRYPTED__",  # answers are encrypted
                "metadata": {
                    "category": row.get("category", "unknown"),
                    "source": "microsoft/LiveDRBench",
                    # Preserve fields needed for LiveDRBench evaluation
                    "key": row.get("key"),
                    "ground_truths_encrypted": row.get("ground_truths", ""),
                    "misc_encrypted": row.get("misc", ""),
                    "canary": row.get("canary", ""),
                },
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Saved {len(raw_data)} entries to {standardized_path}")

    # Also save a schema summary for reference
    if raw_data:
        schema_path = output_path / "schema.json"
        sample = raw_data[0]
        schema = {}
        for k, v in sample.items():
            schema[k] = {
                "type": type(v).__name__,
                "sample": str(v)[:200] if v else None,
            }
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"Saved schema to {schema_path}")

    print("Done! Next: inspect raw_data.json or load in dashboard.")
