# ⚡ Win AI Helper

A lightweight, privacy-first Windows AI assistant that lives in your system tray. Powered by [Ollama](https://ollama.com) for local LLM inference — no cloud, no API keys, no data leaves your machine.

Select or copy any text anywhere in Windows and an AI suggestion bar appears instantly near your cursor with smart actions like **Rewrite**, **Explain**, **Translate**, **Summarize**, and more.

---

## ✨ Features

- **🖥️ System Tray App** — Runs quietly in the background, always one hotkey away
- **📋 Smart Clipboard Monitor** — Detects text selection & copy events across any app and shows a floating AI action bar near your cursor
- **⚡ Quick Bar** — A spotlight-style input window for direct AI conversations
- **🎙️ Voice Input** — Speech-to-text via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (runs locally on CPU)
- **🔊 Text-to-Speech** — Read AI responses aloud (supports English & Tamil)
- **🖼️ Image Generation** — Generate images via local Stable Diffusion / ComfyUI API
- **🧠 Lazy Model Loading** — Ollama model is loaded only when you trigger an action (low RAM usage)
- **📜 History** — Browse and revisit past AI interactions
- **🎯 Custom Skills** — Switch between output directives (Direct Answer, JSON, Code Only, Tanglish, etc.)
- **🔄 Model Switcher** — Switch between installed Ollama models on the fly
- **🌐 Multi-Language Translation** — Tamil, English, Tanglish, Hindi, Malayalam, Telugu, French, German, Spanish, Japanese
- **🚀 Auto Startup** — Optionally launch on Windows boot via registry + startup folder

---

## 🛠️ Setup

### Prerequisites

- **Windows 10/11**
- **Python 3.10+** installed and available in PATH
- **[Ollama](https://ollama.com/download)** installed

### Quick Setup (One-Click)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ilavarasanAppu/Win-AI-Helper.git
   cd Win-AI-Helper
   ```

2. **Launch the application (One-Click):**
   ```
   start.bat
   ```
   This will:
   - Check and install required Python packages silently
   - Start Ollama server (if not already running)
   - Launch the AI Helper app detached in the background
   - Automatically close the terminal window immediately

### Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install PySide6 pynput pyautogui pyperclip pyttsx3 sounddevice numpy faster-whisper Pillow
   ```

2. **Install and start Ollama:**
   ```bash
   ollama serve
   ```

3. **Pull a model** (default: `gemma3:1b-it-qat`):
   ```bash
   ollama pull gemma3:1b-it-qat
   ```

4. **Run the app:**
   ```bash
   python main.py
   ```

### Running & Stopping in Background

- **Start:** Double-click `start.bat` to launch the app silently in the background (terminal auto-closes immediately).
  ```cmd
  start.bat
  ```
- **Stop:** Double-click `stop.bat` to cleanly terminate the background application:
  ```cmd
  stop.bat
  ```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + Alt + G` | Open the **Quick Bar** (spotlight-style AI prompt window) |
| `Ctrl + Alt + X` | Process **clipboard content** with AI (shows nearby action bar) |
| `Ctrl + Alt + V` | Toggle **Voice input** mode (speech-to-text) |

### Automatic Triggers (No Hotkey Needed)

| Trigger | What Happens |
|---|---|
| **Select text** (mouse drag) in any app | A floating AI suggestion bar appears near your cursor |
| **Copy text** (`Ctrl+C`) in any app | The AI suggestion bar appears with smart actions |

---

## 🚀 Usage

### Quick Bar

Press `Ctrl + Alt + G` to open the Quick Bar — a floating, always-on-top window where you can:

- Type any question or request and get an AI response
- Use quick action buttons on selected/clipboard text:
  - **✍️ Rewrite** — Polish and improve text clarity & grammar
  - **✨ Expand** — Enhance text with richer vocabulary and detail
  - **📋 Plan** — Break down objectives into step-by-step plans
  - **📖 Explain** — Get simple, clear explanations of concepts
  - **🌐 Translate** — Translate to/from 10+ languages
  - **📝 Summarize** — Get concise bullet-point summaries
  - **Details** — Get deeper analysis on a topic
- **🎙️ Voice** — Click to start recording, click again to transcribe
- **🔊 Read Aloud** — Have the AI response spoken aloud
- **🖼️ Image** — Generate an image from a text prompt (requires local Stable Diffusion)
- **📋 Copy** — Copy the AI response to clipboard
- **✂️ Clear** — Clear the output area

### Nearby AI Suggestion Bar

When you select or copy text anywhere in Windows, a sleek floating popup appears near your cursor with one-click actions:

- **Rewrite** / **Expand** / **Explain** / **Summarize** / **Plan** / **Translate**
- Click any action to get instant AI results in a compact popup
- Click **Expand ↗** to open the full Quick Bar with the result

### System Tray Menu

Right-click the tray icon (purple ⚡ icon) for:

- 📋 Open Quick Bar
- 📜 View History
- ✂️ AI on Clipboard
- 🎙 Voice Mode
- 🚀 Run on Windows Startup (toggle)
- 📎 Clipboard Monitor (toggle)
- 📦 Current model info

### Custom Skills

Skills are output directives that control how the AI formats responses. Built-in skills:

| Skill | Behavior |
|---|---|
| 🎯 **Direct Answer Only** | Returns only the answer, no fluff |
| 📄 **JSON Format Only** | Returns valid JSON output |
| 🔤 **Tanglish** | Responds in Tanglish (Tamil in English script) |
| 💻 **Code Only** | Returns only executable code blocks |

You can add custom skills from the Quick Bar's skill dropdown.

---

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
  "ollama_url": "http://localhost:11434",
  "default_model": "gemma3:1b-it-qat",
  "keep_alive": "2m",
  "hotkeys": {
    "toggle_quick_bar": "<ctrl>+<alt>+g",
    "process_selection": "<ctrl>+<alt>+x",
    "voice_to_text": "<ctrl>+<alt>+v"
  },
  "sd_api_url": "http://127.0.0.1:7860/sdapi/v1/txt2img",
  "whisper_model_size": "base",
  "tts_rate": 180,
  "enable_clipboard_monitor": true,
  "clipboard_poll_interval_ms": 500
}
```

| Key | Description |
|---|---|
| `ollama_url` | Ollama API endpoint |
| `default_model` | Default Ollama model (auto-falls back if not found) |
| `keep_alive` | How long to keep the model loaded in memory after last request |
| `hotkeys` | Customize keyboard shortcuts |
| `sd_api_url` | Stable Diffusion / ComfyUI API URL for image generation |
| `whisper_model_size` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| `tts_rate` | Text-to-speech speed (words per minute) |
| `enable_clipboard_monitor` | Enable/disable automatic clipboard monitoring |

---

## 📁 Project Structure

```
Win-AI-Helper/
├── main.py              # Entry point — system tray app, hotkeys, clipboard monitor
├── gui_overlay.py       # Quick Bar window, Nearby Suggestion Popup, History dialog
├── ollama_service.py    # Ollama API client with streaming and action prompts
├── audio_service.py     # Speech-to-text (faster-whisper) & text-to-speech
├── image_service.py     # Stable Diffusion / ComfyUI image generation
├── skills.py            # Custom skill/prompt management
├── skills.json          # Saved skills configuration
├── config.json          # App configuration
├── diagnostic.py        # System diagnostics utility
├── start.bat            # One-click background launcher (auto-closing)
├── stop.bat             # Clean shutdown script
└── .gitignore
```

---

## 📄 License

This project is open source. Feel free to use, modify, and distribute.

---

**Made with ❤️ for Windows power users who value privacy and local AI.**
