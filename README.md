# ResolveVoxtral

A DaVinci Resolve script that transcribes your timeline's audio into subtitles, using Mistral's Voxtral Transcribe 2 API. It handles multiple speakers (labeling who's talking when the speaker changes) and works with French or English audio.

**This tool transcribes only — it does not translate.** If your audio is in French, you get French subtitles; if it's in English, you get English subtitles. It's Windows only for now.

> [!IMPORTANT]
> **DaVinci Resolve _Studio_ (the paid version) is required.** ResolveVoxtral builds its window with Fusion's UI scripting toolkit, which Blackmagic **disabled in the free edition starting with Resolve 19.1**. On the free edition the script starts but the window never appears (the console shows a `UIManager`/`'NoneType' object has no attribute 'VGroup'` error). To check which edition you have, open **DaVinci Resolve → About DaVinci Resolve** — the title says "DaVinci Resolve Studio" if you're on Studio.

This guide assumes no prior experience with Python, GitHub, or DaVinci Resolve scripting — every step is spelled out.

## What you'll need

- Windows, with **DaVinci Resolve Studio** already installed (the free edition won't work — see the note above).
- An internet connection.
- A Mistral AI account (free to create) to get an API key — transcription itself is a paid, pay-as-you-go API call (a few tenths of a cent per minute of audio at the time of writing).
- About 10-15 minutes for the one-time setup below.

## Step 1 — Check that Python is installed

DaVinci Resolve scripts run on a Python installed on your computer.

1. Press the **Windows key**, type `cmd`, and press Enter to open Command Prompt.
2. Type `python --version` and press Enter.
   - If you see something like `Python 3.11.4`, you're set — skip to Step 2.
   - If you see an error like "Python is not recognized", download Python from [python.org/downloads](https://www.python.org/downloads/), run the installer, and **make sure to check the box "Add python.exe to PATH"** on the first install screen before clicking Install.

> [!NOTE]
> Resolve works best with a Python version it officially supports (**3.6 through 3.13**). A brand-new release like 3.14 usually still works but is newer than what your Resolve version was tested against, so if you hit odd scripting errors, installing 3.13 is the safest choice.
3. Close and reopen Command Prompt, then run `python --version` again to confirm it worked.

## Step 2 — Install the one required package

ResolveVoxtral needs a small package called `requests` to talk to Mistral's API.

1. In the same Command Prompt window, type:
   ```
   pip install requests
   ```
2. Press Enter and wait for it to finish — you should see a line ending in "Successfully installed requests-...".

If this step fails with a permissions error, try `pip install --user requests` instead.

## Step 3 — Download ResolveVoxtral

1. Go to the [ResolveVoxtral Releases page](../../releases) and download the latest `ResolveVoxtral-vX.X.zip` file.
   - If that page isn't available, use the green **Code** button near the top of this repository's page, then **Download ZIP**, instead.
2. Right-click the downloaded ZIP file and choose **Extract All...**, then extract it anywhere convenient (e.g. your Desktop).

## Step 4 — Copy the script into Resolve's Scripts folder

1. Open the extracted folder — you should see a file named `ResolveVoxtral.py` and a folder named `resolvevoxtral` sitting next to each other. **They must stay together, side by side.**
2. Open File Explorer and paste one of these paths into the address bar. Resolve reads scripts from **one** of two `Scripts` folders depending on your install — try the first, and if the script doesn't show up in Resolve's menu later (Step 6), use the second instead:
   - **Per-user** (paste as-is, it expands automatically):
     ```
     %APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility
     ```
   - **All-users** (note: no "Support" in this one):
     ```
     %PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility
     ```
3. If the `Utility` folder (or the folders above it) doesn't exist yet, create it.
4. Copy **both** `ResolveVoxtral.py` and the `resolvevoxtral` folder into that `Utility` folder.
5. After copying, **fully quit and reopen DaVinci Resolve** — it only scans the Scripts menu at startup, so a new script won't appear until you restart.

> [!TIP]
> You'll also see a `resolvevoxtral` sub-menu full of module names (`app`, `config`, …) under Scripts. That's normal — Resolve lists every sub-folder as a menu. Ignore it and always launch **ResolveVoxtral**.

## Step 5 — Get a Mistral API key

1. Go to [console.mistral.ai](https://console.mistral.ai) and create an account (or log in).
2. Find the **API Keys** section and create a new key.
3. Copy the key somewhere safe for a moment — you'll paste it into ResolveVoxtral next, and won't be able to see it again on Mistral's site afterward.

## Step 6 — First run: enter your API key

1. Open DaVinci Resolve and open (or create) a project.
2. In the top menu, go to **Workspace → Scripts → Utility → ResolveVoxtral**.
3. A small window titled "ResolveVoxtral" appears, asking for your Mistral API key. Paste the key you copied in Step 5 and click **Save**.

You only need to do this once — the key is remembered for future runs. You can change it later via the **Settings** button in the same window.

## Step 7 — Transcribe a timeline

1. Open the timeline you want subtitles for, and make sure it's the active/current timeline in Resolve.
2. Open ResolveVoxtral again (**Workspace → Scripts → Utility → ResolveVoxtral**).
3. Choose a source language from the dropdown — leave it on **Auto** unless you already know the audio is clearly French or English and want to help the transcription along.
4. Click **Transcribe Current Timeline**.
5. Watch the status text — it will move through rendering the timeline's audio, uploading it to Mistral, and building the subtitle file. This can take anywhere from under a minute to several minutes depending on how long your timeline is. Don't close the window while it's working.
6. When it's done, the window shows the full path to your new `.srt` subtitle file.

## Step 8 — Import the subtitles into your timeline

ResolveVoxtral creates the subtitle file but doesn't insert it into your timeline automatically — you do that with Resolve's own, one-click import:

1. In Resolve, go to **File → Import → Subtitle...**
2. Navigate to the path shown in ResolveVoxtral's completion message (by default, a `ResolveVoxtral Output` folder inside your Windows **Documents** folder) and select the `.srt` file.
3. Resolve adds it as a new subtitle track on your timeline.

## Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| `'NoneType' object has no attribute 'VGroup'` in the console, no window opens | You're on the **free** edition of Resolve, which can't show the UI. | Use DaVinci Resolve **Studio**. There's no workaround on the free edition. |
| ResolveVoxtral never appears in Workspace → Scripts | The files are in the Scripts folder Resolve doesn't read, or Resolve wasn't restarted. | Try the other folder location in Step 4, and fully restart Resolve. |
| "No project is open in DaVinci Resolve." | You opened ResolveVoxtral without a project open. | Open a project, then run ResolveVoxtral again. |
| "No timeline is open." | The project has no active timeline. | Open/select a timeline, then run ResolveVoxtral again. |
| "Your Mistral API key was rejected." | The saved key is wrong, expired, or was revoked. | Click **Settings** and paste in a fresh key from console.mistral.ai. |
| "Couldn't reach Mistral's servers." | No internet connection, or a firewall is blocking it. | Check your connection and try again. |
| "Mistral is rate-limiting requests right now." | You've made too many requests too quickly. | Wait a minute or two and try again. |
| "No speech was detected in this timeline." | The rendered audio had no detectable dialogue. | Double check the right timeline/tracks are active, and that dialogue is audible. |
| "Something went wrong. See ... for details." | An unexpected error occurred. | Open the mentioned log file (`%APPDATA%\ResolveVoxtral\log.txt`) for the technical details — worth attaching if you report a bug. |

## Removing ResolveVoxtral

- Delete `ResolveVoxtral.py` and the `resolvevoxtral` folder from the Scripts folder in Step 4.
- Delete the `%APPDATA%\ResolveVoxtral` folder to remove your saved API key and log file.

## Known limitations (v1)

- **DaVinci Resolve Studio only.** The free edition can't display the window (Blackmagic disabled Fusion UI scripting there in Resolve 19.1).
- **Windows only.** macOS/Linux support isn't planned for v1. ([why](docs/adr/0006-windows-only-v1.md))
- **No translation.** Subtitles are produced in the language actually spoken, not translated to a second language. ([why](docs/adr/0001-no-translation-in-v1.md))
- **No automatic subtitle import.** You import the generated `.srt` yourself via Resolve's own File → Import → Subtitle. ([why](docs/adr/0004-manual-srt-import.md))
- **No pre-flight checks on file length.** Very long timelines (beyond Voxtral's ~3 hour per-request limit) aren't validated ahead of time.
- **The window is briefly unresponsive** while rendering/uploading/transcribing — this is expected, not a crash.

## For the curious: how this is built

See [`CONTEXT.md`](CONTEXT.md) for the project's domain glossary, and [`docs/adr/`](docs/adr/) for the reasoning behind each of the non-obvious design decisions above.

## Reporting a bug

Open an issue on this repository's Issues page, and include:
- What you were doing when it happened.
- The exact error message shown.
- If relevant, the contents of `%APPDATA%\ResolveVoxtral\log.txt`.
