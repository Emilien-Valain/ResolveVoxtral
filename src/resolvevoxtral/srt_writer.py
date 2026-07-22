"""Turns diarized transcription segments into a standard .srt file.

See CONTEXT.md for the "Cue" and "Speaker label" definitions this
implements: a new cue starts at every speaker change (even unlabeled),
but the "Speaker N:" prefix is only shown when the speaker differs from
the previous cue, not on every cue.
"""

from dataclasses import dataclass

from .errors import ResolveVoxtralError


@dataclass
class Cue:
    index: int
    start: float
    end: float
    speaker_number: int | None
    show_label: bool
    text: str


def normalize_speakers(segments):
    """Maps raw diarization speaker ids to sequential 1-based numbers,
    assigned in order of first appearance."""
    numbers = {}
    next_number = 1
    for seg in segments:
        if seg.speaker is not None and seg.speaker not in numbers:
            numbers[seg.speaker] = next_number
            next_number += 1
    return numbers


def build_cues(segments):
    if not segments:
        raise ResolveVoxtralError("No speech was detected in this timeline.")

    speaker_numbers = normalize_speakers(segments)
    cues = []
    previous_speaker = object()  # sentinel that can't equal any real speaker or None

    for i, seg in enumerate(segments):
        show_label = seg.speaker is not None and seg.speaker != previous_speaker
        start, end = seg.start, seg.end
        if end <= start:
            end = start + 0.001
        cues.append(Cue(
            index=i + 1,
            start=start,
            end=end,
            speaker_number=speaker_numbers.get(seg.speaker),
            show_label=show_label,
            text=seg.text,
        ))
        previous_speaker = seg.speaker

    return cues


def format_srt_timestamp(seconds):
    total_ms = round(seconds * 1000)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _cue_text(cue):
    if cue.show_label:
        return f"Speaker {cue.speaker_number}:\n{cue.text}"
    return cue.text


def build_srt_text(cues):
    blocks = []
    for cue in cues:
        blocks.append(
            f"{cue.index}\n"
            f"{format_srt_timestamp(cue.start)} --> {format_srt_timestamp(cue.end)}\n"
            f"{_cue_text(cue)}\n"
        )
    return "\n".join(blocks) + "\n"


def write_srt(segments, output_path):
    cues = build_cues(segments)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text(build_srt_text(cues), encoding="utf-8")
    except OSError as e:
        raise ResolveVoxtralError(
            "Couldn't save the subtitle file. Check available disk space and permissions."
        ) from e
    return output_path
