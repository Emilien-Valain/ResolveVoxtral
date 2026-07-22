"""Wraps all access to the DaVinci Resolve scripting API.

This is the one module that cannot be exercised outside of Resolve itself,
so every failure mode here is translated into a plain-language
ResolveEnvironmentError rather than letting an AttributeError on ``None``
bubble up to the GUI.

NOTE: several method/key names below are marked "(verify)" -- they are
believed correct from Resolve's public scripting documentation but should
be double-checked against the API manual shipped with the installed
Resolve version (Support/Developer/Scripting/Docs/ next to the Resolve
install) before release. See the project's implementation plan for the
full checklist.
"""

import time

from .errors import RenderError, ResolveEnvironmentError

RENDER_POLL_INTERVAL_SECONDS = 0.5
RENDER_TIMEOUT_SECONDS = 30 * 60

# (verify) exact extension per AudioCodec choice.
AUDIO_CODEC = "PCM"
AUDIO_FILE_EXTENSION = "wav"


def get_resolve():
    """Returns the Resolve scriptapp object.

    Scripts launched from Resolve's Scripts menu normally have ``bmd``
    injected into their global namespace already, but we go through the
    documented ``DaVinciResolveScript`` module directly so this works
    whether or not that injection happens for this Resolve version.
    """
    try:
        import DaVinciResolveScript as dvr_script
    except ImportError as e:
        raise ResolveEnvironmentError(
            "Couldn't load Resolve's scripting module. Make sure this "
            "script is being run from inside DaVinci Resolve's Scripts menu."
        ) from e

    resolve = dvr_script.scriptapp("Resolve")
    if resolve is None:
        raise ResolveEnvironmentError(
            "Couldn't connect to DaVinci Resolve. Make sure Resolve is "
            "running and this script was launched from its Scripts menu."
        )
    return resolve


def get_current_project(resolve):
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject() if project_manager else None
    if project is None:
        raise ResolveEnvironmentError(
            "No project is open in DaVinci Resolve. Open a project and try again."
        )
    return project


def get_current_timeline(project):
    timeline = project.GetCurrentTimeline()
    if timeline is None:
        raise ResolveEnvironmentError(
            "No timeline is open. Open a timeline in Resolve and try again."
        )
    return timeline


def render_timeline_audio(project, timeline, target_dir, base_name, on_progress=lambda msg: None):
    """Renders the current timeline's audio only (no video) to target_dir.

    Returns the full path to the resulting audio file. Raises RenderError
    on any configuration, render, or timeout failure.
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    ok = project.SetRenderSettings({
        "SelectAllFrames": True,
        "ExportVideo": False,
        "ExportAudio": True,
        "AudioCodec": AUDIO_CODEC,  # (verify)
        "TargetDir": str(target_dir),
        "CustomName": base_name,
    })
    if not ok:
        raise RenderError(
            "DaVinci Resolve rejected the audio render settings. "
            "Make sure a timeline is open and try again."
        )

    job_id = project.AddRenderJob()  # (verify) return shape
    if not job_id:
        raise RenderError("DaVinci Resolve couldn't queue the audio render job.")

    started = project.StartRendering([job_id])  # (verify) signature
    if not started:
        raise RenderError("DaVinci Resolve couldn't start the audio render job.")

    on_progress("Rendering timeline audio...")
    elapsed = 0.0
    while project.IsRenderingInProgress():
        time.sleep(RENDER_POLL_INTERVAL_SECONDS)
        elapsed += RENDER_POLL_INTERVAL_SECONDS
        if elapsed >= RENDER_TIMEOUT_SECONDS:
            project.StopRendering()
            raise RenderError(
                "Rendering the timeline audio is taking too long and was "
                "cancelled. Try again, or with a shorter timeline."
            )
        status = project.GetRenderJobStatus(job_id)  # (verify) key names
        percent = status.get("CompletionPercentage") if status else None
        if percent is not None:
            on_progress(f"Rendering timeline audio... {percent}%")

    status = project.GetRenderJobStatus(job_id)
    job_status = status.get("JobStatus") if status else None  # (verify)
    if job_status != "Complete":
        raise RenderError(
            f"Rendering the timeline audio failed (status: {job_status}). "
            "Try again."
        )

    audio_path = target_dir / f"{base_name}.{AUDIO_FILE_EXTENSION}"
    if not audio_path.exists():
        raise RenderError(
            "The audio render finished but the expected file wasn't found. "
            "Try again."
        )
    return audio_path
