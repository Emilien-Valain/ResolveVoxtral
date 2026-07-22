"""Mistral Voxtral Transcribe 2 API client.

See docs/adr/0001-no-translation-in-v1.md (transcription only, no translation)
and docs/adr/0007-language-override-vs-timestamp-granularities.md (segment
timestamps + diarization always take priority over a manual language pick).

NOTE: the exact model id, the speaker field name, and whether `language` and
`timestamp_granularities` are truly mutually exclusive are all marked
"(verify)" below -- confirm against a live API call before release. See the
project's implementation plan for the full checklist.
"""

from dataclasses import dataclass

import requests

from .errors import TranscriptionError

API_URL = "https://api.mistral.ai/v1/audio/transcriptions"
MODEL = "voxtral-mini-latest"  # (verify) exact current model id for Transcribe 2
REQUEST_TIMEOUT_SECONDS = 600

LANGUAGE_CODES = {
    "french": "fr",
    "english": "en",
}


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None


def transcribe(audio_path, api_key, language_override=None, on_progress=lambda msg: None):
    """Uploads audio_path and returns a chronological list of Segment.

    language_override: None/"auto" to let Voxtral detect the language, or
    "french"/"english" to hint it explicitly.
    """
    headers = {"Authorization": f"Bearer {api_key}"}

    lang_code = None
    if language_override and language_override.lower() != "auto":
        lang_code = LANGUAGE_CODES.get(language_override.lower())

    on_progress("Uploading audio to Mistral...")

    response = _post_transcription(audio_path, headers, lang_code, with_language=bool(lang_code))

    # Segment timestamps + diarization are load-bearing for the whole
    # feature; a manual language hint is a nicety on top. If the API
    # rejects the combination of `language` + `timestamp_granularities`,
    # drop the language hint and retry once rather than losing timestamps.
    if lang_code and response.status_code in (400, 422):
        response = _post_transcription(audio_path, headers, None, with_language=False)

    _raise_for_status(response)

    try:
        data = response.json()
    except ValueError as e:
        raise TranscriptionError(
            "Mistral returned an unexpected response. Please try again."
        ) from e

    segments = [_normalize_segment(seg) for seg in data.get("segments", [])]
    return segments


def _post_transcription(audio_path, headers, lang_code, with_language):
    form_data = {
        "model": MODEL,
        "diarize": "true",
        "timestamp_granularities[]": "segment",
    }
    if with_language and lang_code:
        form_data["language"] = lang_code

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f)}
            return requests.post(
                API_URL,
                headers=headers,
                data=form_data,
                files=files,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
    except requests.exceptions.Timeout as e:
        raise TranscriptionError(
            "Mistral took too long to respond. Try again, or with a shorter timeline."
        ) from e
    except requests.exceptions.ConnectionError as e:
        raise TranscriptionError(
            "Couldn't reach Mistral's servers. Check your internet connection and try again."
        ) from e


def _raise_for_status(response):
    if response.ok:
        return
    if response.status_code in (401, 403):
        raise TranscriptionError(
            "Your Mistral API key was rejected. Open Settings and check that it's correct."
        )
    if response.status_code == 429:
        raise TranscriptionError(
            "Mistral is rate-limiting requests right now. Wait a bit and try again."
        )

    detail = _extract_error_message(response)
    suffix = f" ({detail})" if detail else ""
    raise TranscriptionError(
        f"Mistral's API returned an error (HTTP {response.status_code}){suffix}. "
        "Try again in a few minutes."
    )


def _extract_error_message(response):
    try:
        data = response.json()
    except ValueError:
        return None
    if isinstance(data, dict):
        message = data.get("message") or data.get("error")
        if isinstance(message, dict):
            message = message.get("message")
        if isinstance(message, str):
            return message
    return None


def _normalize_segment(raw):
    speaker = raw.get("speaker") or raw.get("speaker_id")  # (verify) exact field name
    return Segment(
        start=float(raw.get("start", 0.0)),
        end=float(raw.get("end", 0.0)),
        text=(raw.get("text") or "").strip(),
        speaker=speaker,
    )
