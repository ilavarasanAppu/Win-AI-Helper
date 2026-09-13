"""
⚡ Windows AI Helper — System Tray Application
================================================
- Runs in background via system tray (tray icon + hotkey)
- Detects clipboard changes & mouse selection → auto-suggests nearby actions on selected/copied text
- Ollama model loaded lazily only when you trigger an action (low RAM)
- Voice-to-text, text-to-speech, image generation all on-demand
- Hotkeys (Ctrl+Alt+G opens the quick bar; Ctrl+Alt+X processes clipboard; Ctrl+Alt+V voice mode):
    Ctrl+Alt+G      — Open Quick Bar (empty context)
    Ctrl+Alt+X      — Process clipboard selection with AI
    Ctrl+Alt+V      — Voice transcription mode

Usage: start.bat → launches tray icon app in background
       stop.bat  → cleanly stops the background app
"""

import sys
import json
import time
import threading
import os
import winreg

# Ensure safe output encoding under pythonw (where stdout may be None) and Windows cp1252
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
elif hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
elif hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor, QPainter, QCursor
from PySide6.QtCore import QTimer, QObject, Signal


# ── Imports ────────────────────────────────────────────────────
from ollama_service import OllamaService
from audio_service import AudioService
from image_service import ImageService
from gui_overlay import AIHelperWindow, NearbySuggestionPopup, HistoryManager

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Win AI Helper"


def load_config():
    """Load configuration from config.json (next to this file)."""
    try:
        with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as f:
            return json.load(f)
    except Exception:
        return {
            "ollama_url": "http://localhost:11434",
            "default_model": "lfm2.5-thinking:latest",
            "keep_alive": "2m",
            "whisper_model_size": "base",
            "enable_clipboard_monitor": True,
            "auto_startup": False,
        }


# ── Tray icon (drawn programmatically) ────────────────────────
def create_tray_icon():
    pixmap = QPixmap(36, 36)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    # Icon: purple rounded square with lightning bolt shape
    painter.setBrush(QColor("#818cf8"))
    painter.drawRoundedRect(2, 2, 32, 32, 6, 6)
    # Bolt symbol (simple lines)
    painter.setPen(QColor("#e4e4e7"))
    painter.drawLine(8, 10, 22, 10)   # top horizontal
    painter.drawLine(15, 10, 15, 24)  # vertical down
    painter.drawLine(10, 24, 20, 24)  # bottom horizontal
    painter.end()
    return QIcon(pixmap)


# ── Helper: Windows Auto Startup via Registry & Startup folder ─
def is_auto_startup_enabled() -> bool:
    """Check if application is registered in Windows Registry or Startup folder."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        if val:
            return True
    except Exception:
        pass

    startup_dir = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_dir, "Win AI Helper.lnk")
    return os.path.exists(shortcut_path)


def get_pythonw_executable() -> str:
    """Find pythonw.exe path for native windowless GUI execution without terminal allocation."""
    venv_pyw = os.path.expandvars(r"%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe")
    if os.path.exists(venv_pyw):
        return venv_pyw
    py_exe = sys.executable
    if py_exe.lower().endswith("python.exe"):
        pyw = py_exe[:-10] + "pythonw.exe"
        if os.path.exists(pyw):
            return pyw
    return "pythonw.exe"


def set_auto_startup(enable: bool):
    """Enable or disable Windows Auto Startup via Registry and Startup folder shortcut using native pythonw.exe."""
    pythonw_exe = get_pythonw_executable()
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    app_dir = os.path.dirname(main_py)
    target_cmd = f'"{pythonw_exe}" "{main_py}"'

    # 1. Windows Registry (HKCU\Software\Microsoft\Windows\CurrentVersion\Run)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_ALL_ACCESS)
    except Exception:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        except Exception as e:
            print(f"  Registry access error: {e}")
            key = None

    if key:
        try:
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, target_cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        except Exception as e:
            print(f"  Error modifying registry startup: {e}")
        finally:
            winreg.CloseKey(key)

    # 2. Windows Startup folder shortcut (.lnk)
    startup_dir = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_path = os.path.join(startup_dir, "Win AI Helper.lnk")

    if enable:
        try:
            import subprocess
            ps_cmd = (
                f'$ws = New-Object -ComObject WScript.Shell; '
                f'$s = $ws.CreateShortcut("{shortcut_path}"); '
                f'$s.TargetPath = "{pythonw_exe}"; '
                f'$s.Arguments = "`"{main_py}`""; '
                f'$s.WorkingDirectory = "{app_dir}"; '
                f'$s.WindowStyle = 7; '
                f'$s.Save()'
            )
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], capture_output=True)
        except Exception as e:
            print(f"  Error creating startup shortcut: {e}")
    else:
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
            except Exception:
                pass


# ── Helper: get selected text from clipboard ───────────────────
def get_selected_text() -> str:
    """Read the OS clipboard content as a substitute for selected text."""
    try:
        import pyperclip
        text = pyperclip.paste()
        return text.strip() if text else ""
    except Exception:
        return ""


# ── Tray menu builder ─────────────────────────────────────────
def build_tray_menu(window, nearby_popup, config):
    tray = QSystemTrayIcon(create_tray_icon(), QApplication.instance())
    tray.setToolTip("⚡ Win AI Helper — Press Ctrl+Alt+G to open")

    menu = QMenu()

    # --- Open Quick Bar ---
    show_action = QAction("📋  Open Quick Bar (Ctrl+Alt+G)", window)
    show_action.triggered.connect(lambda: window.show_centered())
    menu.addAction(show_action)

    # --- View History ---
    hist_action = QAction("📜  View History", window)
    hist_action.triggered.connect(lambda: window.show_history_dialog())
    menu.addAction(hist_action)

    # --- Process Clipboard Selection ---
    process_action = QAction("✂️  AI on Clipboard (Ctrl+Alt+X)", window)
    def on_process_clipboard():
        text = get_selected_text()
        if text and nearby_popup:
            nearby_popup.show_near_position(text, trigger_type="copy")
        else:
            window.process_clipboard_selection(text)
    process_action.triggered.connect(on_process_clipboard)
    menu.addAction(process_action)

    # --- Voice Mode ---
    voice_action = QAction("🎙  Voice Mode (Ctrl+Alt+V)", window)
    voice_action.triggered.connect(window.toggle_voice_input)
    menu.addAction(voice_action)

    # --- Separator ---
    menu.addSeparator()

    # --- Run on Windows Startup ---
    startup_action = QAction("🚀  Run on Windows Startup", window)
    startup_action.setCheckable(True)
    startup_action.setChecked(is_auto_startup_enabled())

    def on_startup_toggle(checked):
        set_auto_startup(checked)
        config["auto_startup"] = checked
        try:
            with open(os.path.join(os.path.dirname(__file__), "config.json"), "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    startup_action.triggered.connect(on_startup_toggle)
    menu.addAction(startup_action)

    # --- Toggle clipboard monitor ---
    cb_action = QAction("📎  Clipboard Monitor", window)
    cb_action.setCheckable(True)
    cb_action.setChecked(config.get("enable_clipboard_monitor", True))

    def on_clipboard_toggle(checked):
        config["enable_clipboard_monitor"] = checked
        try:
            with open(os.path.join(os.path.dirname(__file__), "config.json"), "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    cb_action.triggered.connect(on_clipboard_toggle)
    menu.addAction(cb_action)

    # --- Model info ---
    model_info = QAction(f"📦  Using: {window.ollama.get_model_name()}", window)
    model_info.setEnabled(False)
    menu.addAction(model_info)

    # --- Separator ---
    menu.addSeparator()

    # --- Quit ---
    quit_action = QAction("✕  Exit", window)
    quit_action.triggered.connect(QApplication.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.show()
    return tray


# ── Thread-safe Hotkey Signal Bridge ───────────────────────────
class HotkeyBridge(QObject):
    toggle_quick_bar_signal = Signal()
    process_selection_signal = Signal()
    voice_to_text_signal = Signal()
    text_selected_signal = Signal(str, int, int)
    text_copied_signal = Signal(str, int, int)


class SelectionMonitor:
    """Monitors mouse drag text selections & Ctrl+C copies across Windows and triggers AI helper popup near selection."""

    def __init__(self, bridge, is_window_active_fn=None):
        self.bridge = bridge
        self.is_window_active_fn = is_window_active_fn
        self.press_pos = None
        self.last_typing_time = 0
        self.last_copied_text = ""
        self._is_internal_copying = False
        self._start_listeners()

    def _start_listeners(self):
        from pynput import mouse, keyboard

        def on_key_press(key):
            if getattr(self, "_is_internal_copying", False):
                return
            self.last_typing_time = time.time()
            # Detect Ctrl+C (char \x03) copy shortcut press
            try:
                if hasattr(key, 'char') and key.char == '\x03':
                    if not (self.is_window_active_fn and self.is_window_active_fn()):
                        threading.Thread(target=self._check_copy_action, daemon=True).start()
            except Exception:
                pass

        try:
            self.key_listener = keyboard.Listener(on_press=on_key_press)
            self.key_listener.daemon = True
            self.key_listener.start()
        except Exception:
            pass

        def on_click(x, y, button, pressed):
            if button == mouse.Button.left:
                if pressed:
                    self.press_pos = (x, y)
                else:
                    if self.press_pos:
                        dx = abs(x - self.press_pos[0])
                        dy = abs(y - self.press_pos[1])
                        # If mouse dragged across text (> 12px horizontal or 10px vertical)
                        if dx > 12 or dy > 10:
                            if time.time() - self.last_typing_time > 0.2:
                                if not (self.is_window_active_fn and self.is_window_active_fn()):
                                    threading.Thread(
                                        target=self._check_selection, args=(x, y), daemon=True
                                    ).start()
                    self.press_pos = None

        try:
            self.mouse_listener = mouse.Listener(on_click=on_click)
            self.mouse_listener.daemon = True
            self.mouse_listener.start()
        except Exception as e:
            print(f"  Selection monitor warning: {e}")

    def _check_selection(self, x, y):
        import pyperclip
        import pyautogui

        try:
            old_cb = pyperclip.paste()
        except Exception:
            old_cb = ""

        self._is_internal_copying = True
        try:
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.08)
        finally:
            self._is_internal_copying = False

        try:
            new_cb = pyperclip.paste()
            if new_cb and new_cb.strip() and new_cb.strip() != old_cb.strip():
                selected = new_cb.strip()
                if len(selected) >= 2:
                    self.bridge.text_selected_signal.emit(selected, x, y)
        except Exception:
            pass

    def _check_copy_action(self):
        import pyperclip
        time.sleep(0.12)
        try:
            cb_text = pyperclip.paste()
            if cb_text and cb_text.strip() and cb_text.strip() != self.last_copied_text:
                self.last_copied_text = cb_text.strip()
                if len(self.last_copied_text) >= 2:
                    self.bridge.text_copied_signal.emit(self.last_copied_text, 0, 0)
        except Exception:
            pass


# ── Global hotkey dispatcher ───────────────────────────────────
def setup_hotkeys(bridge, config):
    from pynput import keyboard

    hotkeys = config.get("hotkeys", {})

    active_hotkeys = {}
    for action_name, key_str in hotkeys.items():
        if action_name == "toggle_quick_bar":
            active_hotkeys[key_str] = bridge.toggle_quick_bar_signal.emit
        elif action_name == "process_selection":
            active_hotkeys[key_str] = bridge.process_selection_signal.emit
        elif action_name == "voice_to_text":
            active_hotkeys[key_str] = bridge.voice_to_text_signal.emit

    print("Global hotkeys registered:")
    for k in sorted(active_hotkeys):
        print(f"  {k}")

    try:
        with keyboard.GlobalHotKeys(active_hotkeys) as h:
            h.join()
    except Exception as e:
        print(f"  Hotkey listener error: {e}")


# ── Main entry point ───────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")

    print("⚡ Win AI Helper starting...")

    # Load config and services (all lightweight at startup)
    config = load_config()

    # Automatically enable Windows auto-startup on first initiation or first run
    if not config.get("first_run_complete", False) or "auto_startup" not in config:
        print("  First initiation detected: enabling Windows Auto Startup...")
        config["auto_startup"] = True
        config["first_run_complete"] = True
        set_auto_startup(True)
        try:
            with open(os.path.join(os.path.dirname(__file__), "config.json"), "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"  Error saving config: {e}")
    elif config.get("auto_startup", True) and not is_auto_startup_enabled():
        print("  Enabling Windows Auto Startup...")
        set_auto_startup(True)

    ollama_svc = OllamaService(
        base_url=config.get("ollama_url", "http://localhost:11434"),
        default_model=config.get("default_model", "lfm2.5-thinking:latest"),
        keep_alive=config.get("keep_alive", "2m")
    )
    print(f"  Using model: {ollama_svc.get_model_name()}")

    audio_svc = AudioService(whisper_size=config.get("whisper_model_size", "base"))
    image_svc = ImageService(api_url=config.get("sd_api_url", "http://127.0.0.1:7860/sdapi/v1/txt2img"))

    history_mgr = HistoryManager()
    window = AIHelperWindow(ollama_svc, audio_svc, image_svc, config, history_manager=history_mgr)
    nearby_popup = NearbySuggestionPopup(ollama_svc, history_manager=history_mgr)

    # Connect thread-safe hotkey bridge signals
    bridge = HotkeyBridge()
    def _on_quick_bar():
        window.selected_text = ""
        window.show_centered()

    def _on_process_selection():
        selected = get_selected_text()
        if selected:
            nearby_popup.show_near_position(selected, trigger_type="copy")
        else:
            window.show_centered()

    bridge.toggle_quick_bar_signal.connect(_on_quick_bar)
    bridge.process_selection_signal.connect(_on_process_selection)
    bridge.voice_to_text_signal.connect(window.toggle_voice_input)

    # Wire text selection & copied signals to Nearby Floating Bar with debouncing
    last_trigger = {"text": "", "time": 0}

    def _on_text_selected(text, x, y):
        now = time.time()
        if text == last_trigger["text"] and (now - last_trigger["time"]) < 0.6:
            return
        last_trigger["text"] = text
        last_trigger["time"] = now
        nearby_popup.show_near_position(text, x, y, trigger_type="selection")

    def _on_text_copied(text, x, y):
        now = time.time()
        if text == last_trigger["text"] and (now - last_trigger["time"]) < 0.6:
            return
        last_trigger["text"] = text
        last_trigger["time"] = now
        nearby_popup.show_near_position(text, x, y, trigger_type="copy")

    def _on_expand_to_main(action, text):
        window.selected_text = text
        window.show_with_context(text)
        window.show_centered()
        if action:
            window.execute_action(action)

    bridge.text_selected_signal.connect(_on_text_selected)
    bridge.text_copied_signal.connect(_on_text_copied)
    nearby_popup.expand_requested.connect(_on_expand_to_main)

    # Start system-wide mouse drag text selection & copy monitor
    selection_mon = SelectionMonitor(
        bridge,
        is_window_active_fn=lambda: window.isActiveWindow() or window.isVisible() or nearby_popup.isVisible()
    )

    # Build tray icon and menu
    build_tray_menu(window, nearby_popup, config)

    # Start global hotkey listener thread
    listener_thread = threading.Thread(
        target=setup_hotkeys, args=(bridge, config), daemon=True
    )
    listener_thread.start()

    print("\n✅ Win AI Helper is running in system tray!")
    print("   Shortcuts: Ctrl+Alt+G (open), Ctrl+Alt+X (clipboard AI), Ctrl+Alt+V (voice)")
    print("   Select or Copy text anywhere in Windows to bring up the nearby AI suggestion bar.")
    print("   Right-click the tray icon to access settings & auto-startup.\n")
    sys.stdout.flush()

    # Keep app alive (tray icon persists after main window close)
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        log_path = os.path.join(os.path.dirname(__file__), "app_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fatal error:\n")
            traceback.print_exc(file=f)
        raise