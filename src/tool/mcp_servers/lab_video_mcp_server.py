# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import os
import json
import tempfile
from fastmcp import FastMCP
from src.logging.logger import setup_mcp_logging
from src.tool.mcp_servers.utils.lab_client import lab_request, lab_request_bytes

LAB_VIDEO_BASE_URL = os.environ.get(
    "LAB_VIDEO_BASE_URL", "https://video.frederickpi.com"
)

setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("lab-video-mcp-server")


def _format_transcript(data: dict) -> str:
    """Format transcript response into readable timestamped text."""
    # The response structure may vary; handle common shapes
    transcript = data.get("transcript") or data.get("text") or data.get("result")

    if isinstance(transcript, list):
        # List of {text, start, duration} entries
        lines = []
        for entry in transcript:
            text = entry.get("text", "")
            start = entry.get("start") or entry.get("offset", 0)
            # Format timestamp as MM:SS
            mins = int(float(start)) // 60
            secs = int(float(start)) % 60
            lines.append(f"[{mins:02d}:{secs:02d}] {text}")
        return "\n".join(lines)

    if isinstance(transcript, str):
        return transcript

    # Fallback: dump the whole response
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_youtube_transcript(
    url: str = "",
    video_id: str = "",
    languages: list[str] | None = None,
) -> str:
    """Extract transcript/subtitles from a YouTube video with timestamps.
    More reliable than scraping for getting YouTube video text content.

    Args:
        url: YouTube video URL (e.g., https://youtube.com/watch?v=xxx).
        video_id: YouTube video ID (alternative to URL, takes priority).
        languages: Preferred transcript languages in order of preference
            (e.g., ['en', 'zh']). Defaults to ['en'].

    Returns:
        Timestamped transcript text of the video.
    """
    if not url and not video_id:
        return "[ERROR]: Either url or video_id must be provided."

    body: dict = {
        "languages": languages or ["en"],
        "save_to_file": False,
        "max_attempts": 10,
    }
    if video_id:
        body["video_id"] = video_id.strip()
    if url:
        body["url"] = url.strip()

    try:
        resp = await lab_request(
            "POST",
            f"{LAB_VIDEO_BASE_URL}/transcript",
            json_body=body,
            timeout=120,
        )
        if isinstance(resp, str):
            if resp.startswith("[ERROR]"):
                return resp
            return resp  # Plain text transcript
        return _format_transcript(resp)
    except Exception as e:
        return f"[ERROR]: Failed to get YouTube transcript: {e}"


@mcp.tool()
async def download_video_audio(
    url: str,
    audio_only: bool = False,
) -> str:
    """Download video or audio from a URL using yt-dlp.
    Supports YouTube, Vimeo, and many other video platforms.
    Returns the local file path to the downloaded content.

    Args:
        url: The video/audio URL to download.
        audio_only: If True, extract audio only (smaller file). Default: False.

    Returns:
        Local file path to the downloaded media file.
    """
    if not url or not url.strip():
        return "[ERROR]: URL cannot be empty."

    cli_args = []
    if audio_only:
        cli_args = ["-x", "--audio-format", "mp3"]

    body: dict = {
        "url": url.strip(),
        "cli_args": cli_args,
        "max_attempts": 10,
    }

    try:
        content_bytes, content_type = await lab_request_bytes(
            "POST",
            f"{LAB_VIDEO_BASE_URL}/download",
            json_body=body,
            timeout=300,
        )

        if not content_bytes:
            return "[ERROR]: Download returned empty response."

        # Determine extension
        ext = ".mp3" if audio_only else ".mp4"
        if "audio" in content_type:
            ext = ".mp3"
        elif "video" in content_type:
            ext = ".mp4"
        elif "webm" in content_type:
            ext = ".webm"

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=ext, prefix="lab_video_"
        ) as f:
            f.write(content_bytes)
            return f.name

    except Exception as e:
        return f"[ERROR]: Video download failed: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
