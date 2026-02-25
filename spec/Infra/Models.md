# Models — LLM Provider Inventory

> All available LLM providers. To switch models for an experiment, change the `defaults` in your agent config YAML.

## Available Providers

| Provider | Config File | Provider Class | Model | Access Via |
|----------|------------|----------------|-------|------------|
| Claude 3.7 Sonnet | `agent_llm_claude37sonnet.yaml` | `ClaudeOpenRouterClient` | `anthropic/claude-3.7-sonnet` | OpenRouter |
| Claude 3.7 Sonnet | `agent_llm_claude37sonnet_anthropic.yaml` | `ClaudeAnthropicClient` | — | Anthropic direct |
| DeepSeek V3.1 | `agent_llm_deepseek_openrouter.yaml` | `DeepSeekOpenRouterClient` | `deepseek/deepseek-chat-v3.1` | OpenRouter |
| GPT-4o | `agent_llm_gpt4o.yaml` | `GPTOpenAIClient` | `gpt-4o` | OpenAI |
| GPT-5 | `agent_llm_gpt5.yaml` | `GPT5OpenAIClient` | `gpt-5` | OpenAI |
| MiroThinker | `agent_llm_mirothinker.yaml` | `MiroThinkerSGLangClient` | (self-hosted) | SGLang |
| Gemini 2.5 Flash | `agent_llm_gemini.yaml` | `ClaudeOpenRouterClient` | `google/gemini-2.5-flash-preview` | OpenRouter |
| Gemini 2.5 Flash | `agent_llm_gemini_direct.yaml` | `GPTOpenAIClient` | `gemini-2.5-flash-preview-05-20` | Google AI direct |
| Qwen3-32B | `agent_llm_qwen3_local.yaml` | `Qwen3LocalClient` | `Qwen/Qwen3-32B` | Local (SGLang) |

## How to Switch Models

In your agent config, change the Hydra defaults or override LLM settings:

```yaml
# Option A: Use a predefined LLM config as defaults base
# (create agent_{benchmark}_{model}.yaml with appropriate defaults)

# Option B: Override in CLI
uv run main.py common-benchmark --config_file_name=agent_gaia-validation_claude37sonnet \
  main_agent.llm.model_name="anthropic/claude-3.7-sonnet"
```

## How to Add a New Provider

1. Create `config/agent_llm_{name}.yaml` with provider class + model params
2. Implement provider class in `src/llm/providers/{name}_client.py` (must implement `LLMProviderClientBase`)
3. Add API key to `.env.template` and `.env`
4. Update this document

## Environment Variables

| Variable | Used By | Required |
|----------|---------|----------|
| `OPENROUTER_API_KEY` | Claude, DeepSeek, Gemini (via OpenRouter) | Yes (default provider) |
| `OPENAI_API_KEY` | GPT-4o, GPT-5, hint generation, eval judging | For OpenAI models |
| `GEMINI_API_KEY` | Gemini direct | For Gemini direct |
| `LOCAL_LLM_API_KEY` | Qwen3 local | For local models |
| `LOCAL_LLM_BASE_URL` | Qwen3 local | For local models |
