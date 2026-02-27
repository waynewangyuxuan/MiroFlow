# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import os
import tempfile
import requests
from urllib.parse import urlparse
from fastmcp import FastMCP
from src.logging.logger import setup_mcp_logging
from src.tool.mcp_servers.utils.lab_client import lab_upload

LAB_AUDIO_BASE_URL = os.environ.get(
    "LAB_AUDIO_BASE_URL", "https://audio.frederickpi.com"
)
# Default model on the Speaches service
LAB_AUDIO_MODEL = os.environ.get(
    "LAB_AUDIO_MODEL", "Systran/faster-whisper-base"
)

setup_mcp_logging(tool_name=os.path.basename(__file__))
mcp = FastMCP("lab-audio-mcp-server")

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".webm"}


def _get_audio_extension(path_or_url: str, content_type: str = "") -> str:
    """Determine audio file extension from URL path or content-type header."""
    parsed = urlparse(path_or_url)
    for ext in AUDIO_EXTENSIONS:
        if parsed.path.lower().endswith(ext):
            return ext
    ct = content_type.lower()
    if "mp3" in ct or "mpeg" in ct:
        return ".mp3"
    if "wav" in ct:
        return ".wav"
    if "m4a" in ct:
        return ".m4a"
    if "ogg" in ct:
        return ".ogg"
    if "flac" in ct:
        return ".flac"
    return ".mp3"


def _download_to_temp(url: str) -> str:
    """Download a URL to a temp file and return the path."""
    resp = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        timeout=120,
    )
    resp.raise_for_status()
    ext = _get_audio_extension(url, resp.headers.get("content-type", ""))
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(resp.content)
        return f.name


@mcp.tool()
async def lab_audio_transcribe(
    audio_path_or_url: str,
    language: str = "",
    response_format: str = "text",
) -> str:
    """Transcribe an audio file to text using Whisper speech recognition.
    Supports 99 languages. No daily quota limit. Does NOT require OpenAI API key.

    Args:
        audio_path_or_url: Local file path or URL of the audio file.
            Supported formats: mp3, wav, m4a, flac, ogg, aac.
            YouTube URLs are NOT supported — use get_youtube_transcript instead.
        language: Optional ISO-639-1 language code (e.g., 'en', 'zh', 'es')
            to improve accuracy. Leave empty for auto-detection.
        response_format: Output format: 'text', 'json', 'verbose_json',
            'srt', or 'vtt' (default: 'text').

    Returns:
        The transcription text, or timestamped output in srt/vtt format.
    """
    if not audio_path_or_url or not audio_path_or_url.strip():
        return "[ERROR]: audio_path_or_url cannot be empty."

    temp_path = None
    try:
        # Resolve file path
        if os.path.exists(audio_path_or_url):
            file_path = audio_path_or_url
        else:
            temp_path = _download_to_temp(audio_path_or_url)
            file_path = temp_path

        file_name = os.path.basename(file_path)
        extra_fields = {
            "model": LAB_AUDIO_MODEL,
            "response_format": response_format,
        }
        if language:
            extra_fields["language"] = language

        result = await lab_upload(
            f"{LAB_AUDIO_BASE_URL}/v1/audio/transcriptions",
            file_path=file_path,
            file_name=file_name,
            extra_fields=extra_fields,
        )

        if isinstance(result, dict):
            return result.get("text", str(result))
        return str(result)

    except requests.RequestException as e:
        return (
            f"[ERROR]: Failed to download audio file: {e}\n"
            "URLs must be publicly accessible. YouTube URLs are not supported."
        )
    except Exception as e:
        return f"[ERROR]: Audio transcription failed: {e}"
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@mcp.tool()
async def lab_audio_translate(
    audio_path_or_url: str,
    response_format: str = "text",
) -> str:
    """Translate audio in any language to English text.
    Useful for understanding audio content in foreign languages.

    Args:
        audio_path_or_url: Local file path or URL of the audio file.
        response_format: Output format: 'text', 'json', 'verbose_json',
            'srt', or 'vtt' (default: 'text').

    Returns:
        English translation of the audio content.
    """
    if not audio_path_or_url or not audio_path_or_url.strip():
        return "[ERROR]: audio_path_or_url cannot be empty."

    temp_path = None
    try:
        if os.path.exists(audio_path_or_url):
            file_path = audio_path_or_url
        else:
            temp_path = _download_to_temp(audio_path_or_url)
            file_path = temp_path

        file_name = os.path.basename(file_path)
        extra_fields = {
            "model": LAB_AUDIO_MODEL,
            "response_format": response_format,
        }

        result = await lab_upload(
            f"{LAB_AUDIO_BASE_URL}/v1/audio/translations",
            file_path=file_path,
            file_name=file_name,
            extra_fields=extra_fields,
        )

        if isinstance(result, dict):
            return result.get("text", str(result))
        return str(result)

    except requests.RequestException as e:
        return f"[ERROR]: Failed to download audio file: {e}"
    except Exception as e:
        return f"[ERROR]: Audio translation failed: {e}"
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
