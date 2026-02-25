# Qwen3-32B Local LLM Provider for MiroFlow
# Connects to a local OpenAI-compatible endpoint (e.g., vLLM/sglang serving Qwen3-32B)
#
# Key characteristics:
# - OpenAI-compatible API at https://localllm.frederickpi.com
# - Thinking mode enabled: model outputs <think>...</think> blocks that must be stripped
# - Short context window (15536 tokens) - requires careful context management
# - Uses XML-based <use_mcp_tool> for tool calls (not native function calling)
# - JSON parsing may fail; retry up to 5 times with <think> stripping

import asyncio
import dataclasses
import json
import os
import re
from typing import Any, Dict, List

import tiktoken
from omegaconf import DictConfig
from openai import AsyncOpenAI, OpenAI
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.llm.provider_client_base import LLMProviderClientBase
from src.llm.providers.claude_openrouter_client import ContextLimitError
from src.logging.logger import bootstrap_logger

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "INFO")
logger = bootstrap_logger(level=LOGGER_LEVEL)

# Regex to strip <think>...</think> blocks (including multiline)
THINK_PATTERN = re.compile(r"<think>[\s\S]*?</think>", re.DOTALL)

# Regex to strip incomplete thinking blocks at the end (model cut off mid-thought)
THINK_INCOMPLETE_PATTERN = re.compile(r"<think>[\s\S]*$", re.DOTALL)


def strip_think_blocks(text: str) -> str:
    """Remove all <think>...</think> blocks from model output.
    Also handles incomplete thinking blocks (no closing tag)."""
    if not text:
        return text
    # First remove complete think blocks
    result = THINK_PATTERN.sub("", text)
    # Then remove any incomplete think block at the end
    result = THINK_INCOMPLETE_PATTERN.sub("", result)
    return result.strip()


@dataclasses.dataclass
class Qwen3LocalClient(LLMProviderClientBase):
    """LLM provider for local Qwen3-32B served via OpenAI-compatible API."""

    def _create_client(self, config: DictConfig):
        """Create configured OpenAI client pointing to local endpoint."""
        api_key = self.cfg.llm.get("local_api_key", "not-needed")
        base_url = self.cfg.llm.get("local_base_url", "https://localllm.frederickpi.com/v1")

        if self.async_client:
            return AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=600,  # shorter timeout for local model
            )
        else:
            return OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=600,
            )

    @retry(
        wait=wait_exponential(multiplier=5, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_not_exception_type(ContextLimitError),
    )
    async def _create_message(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        tools_definitions,
        keep_tool_result: int = -1,
    ):
        """
        Send message to local Qwen3 API.
        Uses XML-based tool calling (MCP style), not native function calling.
        """
        logger.debug(f" Calling Qwen3 Local LLM ({'async' if self.async_client else 'sync'})")

        # Insert system prompt as the first message
        if system_prompt:
            if messages and messages[0]["role"] in ["system", "developer"]:
                messages[0] = {
                    "role": "system",
                    "content": [dict(type="text", text=system_prompt)],
                }
            else:
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": [dict(type="text", text=system_prompt)],
                    },
                )

        messages_copy = self._remove_tool_result_from_messages(
            messages, keep_tool_result
        )

        params = None
        try:
            temperature = self.temperature

            params = {
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": self.max_tokens,
                "messages": messages_copy,
                "stream": False,
            }

            # Add optional parameters
            if self.top_p != 1.0:
                params["top_p"] = self.top_p
            if self.min_p != 0.0:
                params["min_p"] = self.min_p
            if self.top_k != -1:
                params["top_k"] = self.top_k
            if self.repetition_penalty != 1.0:
                params["repetition_penalty"] = self.repetition_penalty

            response = await self._create_completion(params, self.async_client)

            if (
                response is None
                or response.choices is None
                or len(response.choices) == 0
            ):
                logger.debug(f"Qwen3 LLM call failed: response = {response}")
                raise Exception(f"Qwen3 LLM call failed [rare case]: response = {response}")

            if response.choices and response.choices[0].finish_reason == "length":
                logger.debug(
                    "Qwen3 finish_reason is 'length', triggering ContextLimitError"
                )
                raise ContextLimitError(
                    "(finish_reason=length) Response truncated due to maximum context length"
                )

            if (
                response.choices
                and response.choices[0].finish_reason == "stop"
                and response.choices[0].message.content
                and strip_think_blocks(response.choices[0].message.content).strip() == ""
            ):
                logger.debug(
                    "Qwen3 finish_reason is 'stop', but content is empty after stripping think blocks"
                )
                raise Exception("Qwen3 response is empty after stripping think blocks")

            logger.debug(
                f"Qwen3 LLM call finish_reason: {getattr(response.choices[0], 'finish_reason', 'N/A')}"
            )
            return response

        except asyncio.CancelledError:
            logger.debug("[WARNING] Qwen3 API call was cancelled during execution")
            raise Exception("Qwen3 API call was cancelled during execution")
        except ContextLimitError:
            raise
        except Exception as e:
            error_str = str(e)
            if any(
                keyword in error_str
                for keyword in [
                    "Input is too long",
                    "input length and `max_tokens` exceed context limit",
                    "maximum context length",
                    "prompt is too long",
                    "exceeds the maximum length",
                    "exceeds the maximum allowed length",
                    "Input tokens exceed the configured limit",
                    "Requested token count exceeds",
                ]
            ):
                logger.debug(f"Qwen3 Context limit exceeded: {error_str}")
                raise ContextLimitError(f"Context limit exceeded: {error_str}")

            logger.error(
                f"Qwen3 LLM call failed: {str(e)}",
                exc_info=True,
            )
            raise e

    async def _create_completion(self, params: Dict[str, Any], is_async: bool):
        """Helper to create a completion, handling async and sync calls."""
        if is_async:
            return await self.client.chat.completions.create(**params)
        else:
            return self.client.chat.completions.create(**params)

    def _clean_user_content_from_response(self, text: str) -> str:
        """Remove content between \\n\\nUser: and <use_mcp_tool> in assistant response."""
        pattern = r"\n\nUser:.*?(?=<use_mcp_tool>|$)"
        cleaned_text = re.sub(pattern, "", text, flags=re.MULTILINE | re.DOTALL)
        return cleaned_text

    def process_llm_response(
        self, llm_response, message_history, agent_type="main"
    ) -> tuple[str, bool]:
        """Process Qwen3 LLM response, stripping <think> blocks."""

        if not llm_response or not llm_response.choices:
            error_msg = "Qwen3 LLM did not return a valid response."
            logger.error(f"Should never happen: {error_msg}")
            return "", True

        raw_text = llm_response.choices[0].message.content or ""

        # === CRITICAL: Strip <think>...</think> blocks ===
        assistant_response_text = strip_think_blocks(raw_text)

        # Clean up hallucinated user content
        assistant_response_text = self._clean_user_content_from_response(
            assistant_response_text
        )

        if llm_response.choices[0].finish_reason in ("stop", "length"):
            if not assistant_response_text and llm_response.choices[0].finish_reason == "length":
                assistant_response_text = "LLM response is empty. This is likely due to thinking block used up all tokens."

            message_history.append(
                {"role": "assistant", "content": assistant_response_text}
            )
        else:
            logger.error(
                f"Unsupported finish reason: {llm_response.choices[0].finish_reason}"
            )
            assistant_response_text = (
                "Successful response, but unsupported finish reason: "
                + llm_response.choices[0].finish_reason
            )
            message_history.append(
                {"role": "assistant", "content": assistant_response_text}
            )

        logger.debug(f"Qwen3 Response (after think-strip): {assistant_response_text[:500]}...")

        return assistant_response_text, False

    def extract_tool_calls_info(self, llm_response, assistant_response_text):
        """Extract tool call information from Qwen3 response text.
        Qwen3 uses XML-based <use_mcp_tool> tags (same as Claude via OpenRouter)."""
        from src.utils.parsing_utils import parse_llm_response_for_tool_calls

        return parse_llm_response_for_tool_calls(assistant_response_text)

    def update_message_history(
        self, message_history, tool_call_info, tool_calls_exceeded=False
    ):
        """Update message history with tool calls data.
        Uses the same text-based approach as ClaudeOpenRouterClient."""

        # Filter tool call results with type "text"
        tool_call_info = [item for item in tool_call_info if item[1]["type"] == "text"]

        # Separate valid tool calls and bad tool calls
        valid_tool_calls = [
            (tool_id, content)
            for tool_id, content in tool_call_info
            if tool_id != "FAILED"
        ]
        bad_tool_calls = [
            (tool_id, content)
            for tool_id, content in tool_call_info
            if tool_id == "FAILED"
        ]

        total_calls = len(valid_tool_calls) + len(bad_tool_calls)

        output_parts = []

        if total_calls > 1:
            if tool_calls_exceeded:
                output_parts.append(
                    f"You made too many tool calls. I can only afford to process {len(valid_tool_calls)} valid tool calls in this turn."
                )
            else:
                output_parts.append(
                    f"I have processed {len(valid_tool_calls)} valid tool calls in this turn."
                )

            for i, (tool_id, content) in enumerate(valid_tool_calls, 1):
                output_parts.append(f"Valid tool call {i} result:\n{content['text']}")

            for i, (tool_id, content) in enumerate(bad_tool_calls, 1):
                output_parts.append(f"Failed tool call {i} result:\n{content['text']}")
        else:
            for tool_id, content in valid_tool_calls:
                output_parts.append(content["text"])
            for tool_id, content in bad_tool_calls:
                output_parts.append(content["text"])

        merged_text = "\n\n".join(output_parts)

        message_history.append(
            {
                "role": "user",
                "content": [{"type": "text", "text": merged_text}],
            }
        )
        return message_history

    def parse_llm_response(self, llm_response) -> str:
        """Parse Qwen3 LLM response to get text content (with think-strip)."""
        if not llm_response or not llm_response.choices:
            raise ValueError("Qwen3 LLM did not return a valid response.")
        raw = llm_response.choices[0].message.content
        return strip_think_blocks(raw)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count. Qwen3 uses a different tokenizer but we approximate."""
        if not hasattr(self, "encoding"):
            try:
                self.encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                return len(text) // 3  # Qwen tokens are roughly 3 chars

        try:
            return len(self.encoding.encode(text))
        except Exception:
            return len(text) // 3

    def handle_max_turns_reached_summary_prompt(self, message_history, summary_prompt):
        """Handle max turns reached summary prompt."""
        if message_history[-1]["role"] == "user":
            last_user_message = message_history.pop()
            return (
                last_user_message["content"][0]["text"]
                + "\n\n-----------------\n\n"
                + summary_prompt
            )
        else:
            return summary_prompt
