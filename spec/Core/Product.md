# Product — Research Objectives

> What MiroFlow aims to achieve (replaces PRD for research projects).

## Mission

Build a leading-performance, fully open-source research agent system for multi-step internet research, targeting complex challenges like future event prediction.

## Components

| Component | Description | Location |
|-----------|-------------|----------|
| **MiroFlow** | Research agent framework with reproducible SOTA benchmark performance | This repo |
| **MiroThinker** | Open-source agent with native tool-assisted reasoning | [MiroThinker repo](https://github.com/MiroMindAI/mirothinker) |
| **MiroVerse** | 147k premium training data for research agent training | [HuggingFace](https://huggingface.co/datasets/miromind-ai/MiroVerse-v0.1) |

## Target Benchmarks

| Benchmark | Type | Best Known Score |
|-----------|------|-----------------|
| GAIA (validation) | General AI Assistant | 73.94% pass@1 |
| HLE | Hard reasoning | 27.2% |
| HLE-Text-Only | Hard reasoning (text) | 29.5% |
| BrowserComp-EN | Web browsing | 33.2% |
| BrowserComp-ZH | Web browsing (Chinese) | 47.1% |
| xBench-DeepSearch | Deep search | 72.0% |
| FutureX | Future event prediction | #1 ranking |

## Research Direction

- Replace infra components (LLM, search, tools) with alternatives
- Benchmark each configuration change
- Iterate on agent architecture and prompt design
- Achieve reproducible, measurable improvements
