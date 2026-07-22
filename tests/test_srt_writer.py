import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from resolvevoxtral.errors import ResolveVoxtralError
from resolvevoxtral.srt_writer import build_cues, build_srt_text, format_srt_timestamp
from resolvevoxtral.transcription import Segment


def seg(start, end, text, speaker):
    return Segment(start=start, end=end, text=text, speaker=speaker)


def test_first_cue_with_known_speaker_is_labeled():
    cues = build_cues([seg(0, 1, "hello", "SPEAKER_00")])
    assert cues[0].show_label is True
    assert cues[0].speaker_number == 1


def test_same_speaker_run_labels_only_first():
    cues = build_cues([
        seg(0, 1, "a", "SPEAKER_00"),
        seg(1, 2, "b", "SPEAKER_00"),
        seg(2, 3, "c", "SPEAKER_00"),
    ])
    assert [c.show_label for c in cues] == [True, False, False]


def test_alternating_speakers_label_every_change():
    cues = build_cues([
        seg(0, 1, "a", "SPEAKER_00"),
        seg(1, 2, "b", "SPEAKER_01"),
        seg(2, 3, "c", "SPEAKER_00"),
    ])
    assert [c.show_label for c in cues] == [True, True, True]
    assert [c.speaker_number for c in cues] == [1, 2, 1]


def test_unlabeled_speaker_never_gets_a_label():
    cues = build_cues([
        seg(0, 1, "a", None),
        seg(1, 2, "b", None),
    ])
    assert [c.show_label for c in cues] == [False, False]
    assert [c.speaker_number for c in cues] == [None, None]


def test_transition_to_and_from_none_speaker_counts_as_change():
    cues = build_cues([
        seg(0, 1, "a", "SPEAKER_00"),
        seg(1, 2, "b", None),
        seg(2, 3, "c", "SPEAKER_00"),
    ])
    # None speaker is never itself labeled, but returning to a known speaker
    # after an unlabeled stretch re-triggers the label.
    assert [c.show_label for c in cues] == [True, False, True]


def test_empty_segments_raises():
    with pytest.raises(ResolveVoxtralError):
        build_cues([])


@pytest.mark.parametrize("seconds,expected", [
    (0, "00:00:00,000"),
    (1.5, "00:00:01,500"),
    (61, "00:01:01,000"),
    (3725.4, "01:02:05,400"),
])
def test_format_srt_timestamp(seconds, expected):
    assert format_srt_timestamp(seconds) == expected


def test_build_srt_text_includes_label_only_on_change():
    cues = build_cues([
        seg(0, 1, "Hello there.", "SPEAKER_00"),
        seg(1, 2, "Hi!", "SPEAKER_01"),
        seg(2, 3, "Still me.", "SPEAKER_01"),
    ])
    text = build_srt_text(cues)
    assert "Speaker 1:\nHello there." in text
    assert "Speaker 2:\nHi!" in text
    assert "Speaker 2:\nStill me." not in text
    assert "\nStill me." in text
