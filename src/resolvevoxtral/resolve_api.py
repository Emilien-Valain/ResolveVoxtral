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


def _find_injected(name):
    """Look up a global that Resolve injects into the launching script.

    When a script runs from Resolve's Scripts menu, objects like ``resolve``
    and ``bmd`` are injected into the entry script's namespace (``__main__``)
    -- not into this module -- and are sometimes reachable via ``builtins``.
    """
    import __main__
    obj = getattr(__main__, name, None)
    if obj is not None:
        return obj
    import builtins
    return getattr(builtins, name, None)


def get_resolve():
    """Returns the Resolve scriptapp object.

    Scripts launched from Resolve's Scripts menu get the API through injected
    globals (``resolve`` / ``bmd``), not through the ``DaVinciResolveScript``
    helper module -- that module is only importable when the
    ``RESOLVE_SCRIPT_*`` environment variables are set (the external-scripting
    setup). Try the in-app paths first, then fall back to the module.
    """
    # 1. `resolve` injected directly into the launching script's namespace.
    resolve = _find_injected("resolve")
    if resolve is not None:
        return resolve

    # 2. `bmd.scriptapp("Resolve")` -- bmd is injected in the Fusion
    #    scripting context that the Scripts menu runs scripts in.
    bmd = _find_injected("bmd")
    if bmd is None:
        try:
            import bmd
        except ImportError:
            bmd = None
    if bmd is not None:
        resolve = bmd.scriptapp("Resolve")
        if resolve is not None:
            return resolve

    # 3. The DaVinciResolveScript helper module (external / env-var setups).
    try:
        import DaVinciResolveScript as dvr_script
        resolve = dvr_script.scriptapp("Resolve")
        if resolve is not None:
            return resolve
    except ImportError:
        pass

    raise ResolveEnvironmentError(
        "Couldn't connect to DaVinci Resolve's scripting API. Make sure this "
        "script is launched from Resolve's Scripts menu (Workspace -> "
        "Scripts), and that your Resolve version allows scripting."
    )


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
