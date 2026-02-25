#!/usr/bin/env python3
"""
Convert MiroFlow benchmark results → LiveDRBench predictions.json

MiroFlow saves results as benchmark_results.jsonl with one JSON object per line.
Each object has: task_id, model_boxed_answer, model_response, metadata, etc.

LiveDRBench evaluate.py expects predictions.json:
[
  {"key": <int or null>, "preds": <parsed JSON from agent output>},
  ...
]

Usage (from project root):
    uv run python utils/livedrbench_export.py \\
        --results_dir logs/livedrbench/gemini_direct \\
        --data_file data/livedrbench/standardized_data.jsonl \\
        --output predictions.json

Then evaluate:
    cd LiveDRBench  # cloned repo
    python src/evaluate.py \\
        --openai_api_key $OPENAI_API_KEY \\
        --preds_file ../MiroFlow/predictions.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


def extract_json_from_text(text: str):
    """
    Try to extract a JSON array or object from agent output text.
    The agent is instructed to output JSON, but it may be wrapped in
    markdown code blocks, \boxed{}, or have surrounding prose.
    """
    if not text:
        return []

    # 1. Try: extract from \boxed{...}
    boxed_match = re.search(r'\\boxed\{(.+)\}', text, re.DOTALL)
    if boxed_match:
        text = boxed_match.group(1)

    # 2. Try: extract from ```json ... ``` code blocks
    code_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', text)
    if code_match:
        text = code_match.group(1)

    # 3. Try: find the outermost [ ... ] or { ... }
    # Find first [ or {
    for start_idx, char in enumerate(text):
        if char in '[{':
            break
    else:
        # No JSON structure found, return the raw text as a single prediction
        return [text.strip()] if text.strip() else []

    # Find matching end
    end_char = ']' if text[start_idx] == '[' else '}'
    depth = 0
    end_idx = start_idx
    for i in range(start_idx, len(text)):
        if text[i] == text[start_idx]:
            depth += 1
        elif text[i] == end_char:
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    json_str = text[start_idx:end_idx + 1]

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return [parsed]
        else:
            return [parsed]
    except json.JSONDecodeError:
        # Try to fix common issues: trailing commas, single quotes
        cleaned = re.sub(r',\s*([}\]])', r'\1', json_str)  # remove trailing commas
        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            # Last resort: return raw text
            print(f"  Warning: Could not parse JSON, using raw text")
            return [text.strip()]


def load_task_metadata(data_file: str) -> dict:
    """Load task metadata (key, category) from standardized_data.jsonl."""
    tasks = {}
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            row = json.loads(line.strip())
            task_id = row['task_id']
            tasks[task_id] = {
                'key': row.get('metadata', {}).get('key'),
                'category': row.get('metadata', {}).get('category', 'unknown'),
            }
    return tasks


def convert(results_dir: str, data_file: str, output: str):
    """Convert MiroFlow results to LiveDRBench predictions format."""
    results_path = Path(results_dir) / 'benchmark_results.jsonl'
    if not results_path.exists():
        print(f"Error: {results_path} not found")
        sys.exit(1)

    task_meta = load_task_metadata(data_file)

    # Load MiroFlow results
    results = []
    with open(results_path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line.strip()))

    print(f"Loaded {len(results)} results from {results_path}")

    # Convert to LiveDRBench format
    predictions = []
    for r in results:
        task_id = r['task_id']
        meta = task_meta.get(task_id, {})

        # Extract the agent's answer — prefer boxed_answer, fall back to full response
        answer_text = r.get('model_boxed_answer', '') or r.get('model_response', '')
        preds = extract_json_from_text(answer_text)

        pred_entry = {
            'key': meta.get('key'),
            'preds': preds,
        }
        predictions.append(pred_entry)

        category = meta.get('category', '?')
        n_preds = len(preds) if isinstance(preds, list) else 1
        print(f"  {task_id} [{category}]: {n_preds} predictions extracted")

    # Save
    output_path = Path(output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(predictions)} predictions to {output_path}")
    print(f"\nNext: run LiveDRBench evaluation:")
    print(f"  cd LiveDRBench")
    print(f"  python src/evaluate.py --openai_api_key $OPENAI_API_KEY --preds_file {output_path.absolute()}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert MiroFlow results to LiveDRBench format')
    parser.add_argument('--results_dir', required=True, help='Path to MiroFlow results directory')
    parser.add_argument('--data_file', default='data/livedrbench/standardized_data.jsonl',
                        help='Path to standardized_data.jsonl')
    parser.add_argument('--output', default='predictions.json', help='Output predictions file')
    args = parser.parse_args()
    convert(args.results_dir, args.data_file, args.output)
