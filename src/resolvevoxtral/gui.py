"""Fusion UIManager dialog: view layer only.

No business logic, no HTTP calls, no Resolve render calls live here --
this module just builds the window and forwards user actions to the
callbacks it's given, and exposes small setters so app.py can update
status/error text and busy state.

NOTE: `bmd` is expected to be available because Resolve injects it when a
script is run from its Scripts menu. The lookup below is defensive
(tries a plain `import bmd`, falls back to the builtins namespace) since
this is one of the "verify at implementation time" items in the plan.
Whether UIManager elements support a `Visible` property to toggle between
the first-run and main views the way this module assumes should also be
confirmed against a live Resolve instance.
"""

from .errors import ResolveEnvironmentError

LANGUAGE_OPTIONS = ["Auto", "French", "English"]


def _find_injected(name):
    """Look up a global Resolve injects into the launching script.

    Objects like ``bmd``, ``fusion`` and ``fu`` are injected into the entry
    script's namespace (``__main__``) -- not into this module -- and are
    sometimes also reachable via ``builtins``.
    """
    import __main__
    obj = getattr(__main__, name, None)
    if obj is not None:
        return obj
    import builtins
    return getattr(builtins, name, None)


def _get_bmd():
    bmd = _find_injected("bmd")
    if bmd is not None:
        return bmd
    try:
        import bmd
        return bmd
    except ImportError:
        pass
    raise ResolveEnvironmentError(
        "Run this script from DaVinci Resolve's Scripts menu, not directly with Python."
    )


def _get_ui_manager(resolve, bmd):
    """Return Fusion's UIManager, however this Resolve exposes it.

    In the Scripts-menu context the injected ``fusion``/``fu`` global is the
    UI-capable Fusion instance; ``resolve.Fusion()`` can hand back an object
    whose ``UIManager`` is ``None``. Try the injected globals and
    ``bmd.scriptapp("Fusion")`` before falling back to ``resolve.Fusion()``.
    """
    candidates = [
        _find_injected("fusion"),
        _find_injected("fu"),
        bmd.scriptapp("Fusion"),
    ]
    if resolve is not None:
        candidates.append(resolve.Fusion())

    for fusion in candidates:
        if fusion is None:
            continue
        ui = getattr(fusion, "UIManager", None)
        if ui is not None:
            return fusion, ui

    raise ResolveEnvironmentError(
        "Couldn't access DaVinci Resolve's Fusion UI system. Make sure this "
        "script is launched from Resolve's Scripts menu (Workspace -> Scripts)."
    )


class MainWindow:
    def __init__(self, resolve, callbacks):
        self.callbacks = callbacks
        bmd = _get_bmd()
        self.fusion, self.ui = _get_ui_manager(resolve, bmd)
        self.dispatcher = bmd.UIDispatcher(self.ui)

        ui = self.ui
        self.win = self.dispatcher.AddWindow(
            {"ID": "ResolveVoxtralWindow", "WindowTitle": "ResolveVoxtral", "Geometry": [100, 100, 420, 260]},
            ui.VGroup({"ID": "root"}, [
                ui.VGroup({"ID": "setupGroup"}, [
                    ui.Label({"Text": "Enter your Mistral API key:"}),
                    ui.LineEdit({"ID": "apiKeyField", "PasswordEcho": True}),
                    ui.Button({"ID": "saveKeyButton", "Text": "Save"}),
                ]),
                ui.VGroup({"ID": "mainGroup"}, [
                    ui.Label({"Text": "Source language:"}),
                    ui.ComboBox({"ID": "languageBox"}),
                    ui.Button({"ID": "runButton", "Text": "Transcribe Current Timeline"}),
                    ui.Button({"ID": "settingsButton", "Text": "Settings"}),
                ]),
                ui.Label({"ID": "statusLabel", "Text": "", "WordWrap": True}),
            ])
        )

        items = self.win.Find("languageBox")
        for option in LANGUAGE_OPTIONS:
            items.AddItem(option)

        self.win.On.ResolveVoxtralWindow.Close = self._on_close
        self.win.On.saveKeyButton.Clicked = self._on_save_key_clicked
        self.win.On.runButton.Clicked = self._on_run_clicked
        self.win.On.settingsButton.Clicked = self._on_settings_clicked

    def show_setup_view(self):
        self.win.Find("setupGroup").Visible = True
        self.win.Find("mainGroup").Visible = False

    def show_main_view(self):
        self.win.Find("setupGroup").Visible = False
        self.win.Find("mainGroup").Visible = True

    def get_language_selection(self):
        return self.win.Find("languageBox").CurrentText

    def set_status(self, text):
        self.win.Find("statusLabel").Text = text

    def set_error(self, text):
        self.set_status(f"Error: {text}")

    def set_busy(self, is_busy):
        self.win.Find("runButton").Enabled = not is_busy
        self.win.Find("settingsButton").Enabled = not is_busy

    def run(self):
        self.win.Show()
        self.dispatcher.RunLoop()
        self.win.Hide()

    def _on_close(self, event):
        self.dispatcher.ExitLoop()

    def _on_save_key_clicked(self, event):
        key = self.win.Find("apiKeyField").Text
        self.callbacks.on_save_api_key(key)

    def _on_run_clicked(self, event):
        self.callbacks.on_run_clicked()

    def _on_settings_clicked(self, event):
        self.show_setup_view()
