"""Orchestration: wires GUI events to the render -> transcribe -> write-SRT pipeline.

This is the one module with a broad `except Exception` boundary, per the
product decision that the end user should never see a raw traceback
(docs/adr/0002-gui-dialog-not-console.md).
"""

import tempfile
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

from . import config, resolve_api, srt_writer, transcription
from .errors import ResolveVoxtralError
from .gui import MainWindow


@dataclass
class Callbacks:
    on_save_api_key: object
    on_run_clicked: object


class App:
    def __init__(self):
        self.resolve = resolve_api.get_resolve()
        self.window = MainWindow(self.resolve, Callbacks(
            on_save_api_key=self.on_save_api_key,
            on_run_clicked=self.on_run_clicked,
        ))

    def start(self):
        if config.get_api_key():
            self.window.show_main_view()
        else:
            self.window.show_setup_view()
        self.window.run()

    def on_save_api_key(self, key):
        key = (key or "").strip()
        if not key:
            self.window.set_error("Please enter your Mistral API key.")
            return
        try:
            config.set_api_key(key)
        except ResolveVoxtralError as e:
            self.window.set_error(e.user_message)
            return
        self.window.set_status("API key saved.")
        self.window.show_main_view()

    def on_run_clicked(self):
        self.window.set_busy(True)
        try:
            srt_path = self._run_pipeline()
            self.window.set_status(
                f"Done. Subtitles saved to:\n{srt_path}\n\n"
                "Import this file manually via File → Import → Subtitle."
            )
        except ResolveVoxtralError as e:
            self.window.set_error(e.user_message)
        except Exception:
            self._log_traceback()
            self.window.set_error(
                f"Something went wrong. See {config.get_log_path()} for details."
            )
        finally:
            self.window.set_busy(False)

    def _run_pipeline(self):
        api_key = config.get_api_key()
        if not api_key:
            raise ResolveVoxtralError("No Mistral API key is saved yet. Open Settings first.")

        language_override = self.window.get_language_selection()

        self.window.set_status("Connecting to DaVinci Resolve...")
        project = resolve_api.get_current_project(self.resolve)
        timeline = resolve_api.get_current_timeline(project)

        run_dir = Path(tempfile.gettempdir()) / "ResolveVoxtral" / str(int(time.time()))
        base_name = _sanitize_filename(timeline.GetName()) or "timeline_audio"

        audio_path = resolve_api.render_timeline_audio(
            project, timeline, run_dir, base_name, on_progress=self.window.set_status,
        )

        segments = transcription.transcribe(
            audio_path, api_key, language_override, on_progress=self.window.set_status,
        )

        self.window.set_status("Building subtitle file...")
        srt_path = Path.home() / "Documents" / "ResolveVoxtral Output" / f"{base_name}.srt"
        srt_writer.write_srt(segments, srt_path)

        return srt_path

    def _log_traceback(self):
        try:
            log_path = config.get_log_path()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f.write(traceback.format_exc())
                f.write("\n")
        except OSError:
            pass


def _sanitize_filename(name):
    if not name:
        return ""
    return "".join(c for c in name if c.isalnum() or c in " _-").strip()


def main():
    App().start()
