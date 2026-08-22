"""
Diagnostic tool — run this once to see exactly what is/failing in your system:
    python diagnostic.py

It checks (non-interactively where possible):
  1. Python + required packages import cleanly
  2. Clipboard access via pyperclip (write a unique marker, read it back)
  3. Ollama server connectivity (/api/tags) and installed models
  4. Which pynput global hotkeys are currently capturable

NOTE: This script is interactive for the LAST part (it will ask you to press a
custom key combo once). Press Ctrl+C at any time to stop.
"""

import os
import sys
import json
import time
import traceback


def banner(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


# ── 1. Package import check ────────────────────────────────────
banner("STEP 1 — Python packages")
required = [
    "PySide6", "pynput", "pyautogui", "pyperclip",
    "pyttsx3", "sounddevice", "numpy", "PIL",
]
problems = []
for mod in required:
    try:
        __import__(mod)
        print(f"  OK   {mod}")
    except Exception as e:
        problems.append(mod)
        print(f"  FAIL {mod} -> {type(e).__name__}: {e}")

# Try importing the actual service modules
service_imports = {
    "ollama_service": ("ollama_service", []),
    "audio_service": ("audio_service", ["numpy"]),
    "image_service": ("image_service", []),
}
for name, (modname, needs) in service_imports.items():
    ok = True
    for n in needs:
        try:
            __import__(n)
        except Exception as e:
            print(f"  WARN {name} needs {n}: MISSING ({e})")
            ok = False
    try:
        __import__(modname)
        print(f"  OK   import {modname}")
    except Exception as e:
        problems.append(modname)
        print(f"  FAIL import {modname} -> {type(e).__name__}: {e}")

try:
    from gui_overlay import AIHelperWindow
    print("  OK   import gui_overlay.AIHelperWindow")
except Exception as e:
    # Likely a QApplication-not-instantiated error — acceptable for diagnostics
    msg = str(e).splitlines()[0] if str(e) else repr(e)
    print(f"  INFO import gui_overlay skipped ({msg})")

if problems:
    print("  => Missing packages:", ", ".join(problems))
else:
    print("  => All imports OK.")


# ── 2. Clipboard access check ───────────────────────────────────
banner("STEP 2 — Clipboard (pyperclip) round-trip")
import pyperclip

marker = f"WINAIHELPER_MARKER_{int(time.time()*1000)}_UNIQUE"
try:
    pyperclip.copy(marker)
except Exception as e_copy:
    print(f"  FAIL copy() raised {type(e_copy).__name__}: {e_copy}")
    # Fall back to a raw ctypes attempt info
    try:
        import ctypes
        windll = ctypes.windll.user32  # noqa
        from ctypes import wintypes
        cb_size = wintypes.INT(0)
        win32error = ctypes.wintypes.ERROR(0)
        if not windll.openclipboard(win32error, True):
            print("       (open clipboard failed — access denied)")
    except Exception:
        pass
else:
    time.sleep(0.15)
    try:
        got = pyperclip.paste()
        if got == marker:
            print(f"  OK   round-trip works -> '{got[:20]}...'")
        else:
            print(f"  WARN copy ok but read back != marker (got {len(got)} chars)")
    except Exception as e_read:
        print(f"  FAIL paste() raised {type(e_read).__name__}: {e_read}")

print("  NOTE: If clipboard is denied here, the tray app usually still works when")
print("        launched normally (Qt holds a desktop-clipboard token). This only")
print("        fails from an elevated/console script.")


# ── 3. Ollama connectivity ───────────────────────────────────────
banner("STEP 3 — Ollama server (/api/tags)")
import urllib.request, urllib.error

ollama_up = False
models = []
try:
    req = urllib.request.Request(
        "http://localhost:11434/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    ollama_up = True
    if isinstance(data, list):
        models = [m.get("name") for m in data]
    elif isinstance(data, dict):
        models = [m.get("name") for m in data.get("models", [])]
except urllib.error.HTTPError:
    pass
except Exception as e:
    pass

if ollama_up:
    print(f"  OK   Ollama reachable at http://localhost:11434")
    if models:
        print(f"  Models installed ({len(models)}):")
        for m in models[:8]:
            print(f"      - {m}")
    else:
        print("  WARN server up but no models listed.")
else:
    print("  FAIL Ollama NOT reachable — 'ollama serve' is likely not running.")
    print("         Fix: run in a terminal -> ollama serve --model lfm2.5-thinking:latest")

# ── 4. pynput hotkey capability (needs you!) ───────────────────
banner("STEP 4 — Global hotkeys (interactive)")
print("This part needs a live human + running app.")
print()
print("  The Ctrl+Alt+G (or old Ctrl+Alt+F7) combo is NOT blocked by Windows.")
print("  If it still doesn't fire, make sure no other app (Discord, Steam, etc.)")
print("  is registering the same global hotkey.")
print()
print("  (Live key-press test is skipped in non-interactive runs.)")
