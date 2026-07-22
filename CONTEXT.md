# ResolveVoxtral

A DaVinci Resolve script that transcribes timeline audio into subtitles using Mistral's Voxtral Transcribe 2 API, for French- or English-language footage with multiple speakers.

## Language

**Transcription**:
Converting spoken audio into text in the language it was spoken. This project transcribes only — it never translates.
_Avoid_: Translation (a distinct, out-of-scope operation)

**Cue**:
A single subtitle entry with a start time, end time, and text. A new cue always starts when the speaker changes, whether or not a label is shown.
_Avoid_: Subtitle line, segment

**Speaker**:
A distinct voice identified by Voxtral's diarization within a source recording, numbered (Speaker 1, Speaker 2, ...) in order of appearance.
_Avoid_: Talker, participant

**Speaker label**:
The visible "Speaker N:" prefix on a cue. Shown only when the speaker differs from the previous cue, not on every cue.

**Source language**:
The language actually spoken in the audio — detected automatically by Voxtral, or set manually by the user as an override. There is no translation target; this is not a source/target pair.

**Settings**:
The user's locally stored configuration — currently just the Mistral API key — persisted in a plaintext local file and entered once via the GUI dialog.
