# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
from fastmcp import FastMCP
from src.logging.logger import setup_mcp_logging
from src.tool.mcp_servers.utils.lab_client import lab_request

LAB_PSYCHOLING_BASE_URL = os.environ.get(
    "LAB_PSYCHOLING_BASE_URL", "https://psycholing.frederickpi.com"
)

setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("lab-psycholing-mcp-server")


def _format_analysis(data: dict) -> str:
    """Format psycholinguistic analysis results into readable text."""
    if not data:
        return "No analysis data returned."
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def analyze_text_psycholinguistics(
    text: str,
    article_id: str = "",
) -> str:
    """Analyze text for psycholinguistic features using lexicon-based methods.
    Returns numeric features for concreteness, emotion, sensory norms,
    socialness, age of acquisition, and LIWC-style categories.
    This is NOT LLM-based — it uses established psycholinguistic lexicons.

    Args:
        text: The text to analyze (minimum 1 character).
        article_id: Optional identifier for tracking the analysis.

    Returns:
        Psycholinguistic feature scores including concreteness, emotion,
        sensory norms, socialness, and age of acquisition statistics.
    """
    if not text or not text.strip():
        return "[ERROR]: Text cannot be empty."

    body = {
        "articles": [
            {"text": text.strip(), "id": article_id or "analysis-1"}
        ]
    }

    try:
        resp = await lab_request(
            "POST",
            f"{LAB_PSYCHOLING_BASE_URL}/analyze",
            json_body=body,
        )
        if isinstance(resp, str):
            return resp

        if not resp.get("success"):
            error = resp.get("error") or resp.get("message") or "Unknown error"
            return f"[ERROR]: Analysis failed: {error}"

        data = resp.get("data")
        processing_time = resp.get("processing_time_ms", 0)
        result = _format_analysis(data)
        return f"Processing time: {processing_time:.0f}ms\n\n{result}"

    except Exception as e:
        return f"[ERROR]: Psycholinguistic analysis failed: {e}"


@mcp.tool()
async def analyze_texts_psycholinguistics(
    texts: list[str],
) -> str:
    """Analyze multiple texts for psycholinguistic features in a single batch.
    Useful for comparing psycholinguistic properties across documents.

    Args:
        texts: List of texts to analyze (each minimum 1 character).

    Returns:
        Psycholinguistic feature scores for each text.
    """
    if not texts:
        return "[ERROR]: Text list cannot be empty."

    articles = [
        {"text": t.strip(), "id": f"text-{i + 1}"}
        for i, t in enumerate(texts)
        if t and t.strip()
    ]
    if not articles:
        return "[ERROR]: No valid texts provided."

    body = {"articles": articles}

    try:
        resp = await lab_request(
            "POST",
            f"{LAB_PSYCHOLING_BASE_URL}/analyze",
            json_body=body,
        )
        if isinstance(resp, str):
            return resp

        if not resp.get("success"):
            error = resp.get("error") or resp.get("message") or "Unknown error"
            return f"[ERROR]: Batch analysis failed: {error}"

        data = resp.get("data")
        processing_time = resp.get("processing_time_ms", 0)
        result = _format_analysis(data)
        return f"Processing time: {processing_time:.0f}ms\nTexts analyzed: {len(articles)}\n\n{result}"

    except Exception as e:
        return f"[ERROR]: Batch psycholinguistic analysis failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
