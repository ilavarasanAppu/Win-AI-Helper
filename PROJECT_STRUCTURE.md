# ⚡ Win AI Helper — Complete Project Structure & File Documentation

> **Privacy-first, local LLM Windows assistant — lives in system tray, powered by Ollama. No cloud, no API keys.**
> Generated: 2026-09-24 | Location: `C:\Github\Win-AI-Helper`

---

## 1. At-a-Glance

| Attribute | Value |
|---|---|
| **Type** | Windows System Tray App (PySide6 Qt) |
| **Language** | Python 3.10+ |
| **LLM** | Ollama (`http://localhost:11434`, lazy-loaded) — default `gemma3:1b-it-qat` |
| **STT** | `faster-whisper` (base, CPU int8, VAD) |
| **TTS** | `pyttsx3` (SAPI) + Google TTS fallback (ta/en chunk 150 chars) |
| **Imaging** | Stable Diffusion WebUI (`sdapi/v1/txt2img`) / ComfyUI fallback |
| **Hotkeys** | `Ctrl+Alt+G` Quick Bar, `Ctrl+Alt+X` Clipboard AI, `Ctrl+Alt+V` Voice |
| **Auto-start** | Registry `HKCU\...\Run` + Startup `.lnk` via `pythonw.exe` |
| **Start / Stop** | `start.bat` (hidden `pythonw`) / `stop.bat` (ps kill `*main.py*`) |

---

## 2. Folder Tree

```
Win-AI-Helper/
├── main.py                 529 lines — entry, tray, hotkeys, selection monitor
├── gui_overlay.py         ~1570 lines — UI: Quick Bar, Nearby Popup, History, Writing Assist
├── ollama_service.py       ~230 lines — Ollama API client, streaming, action prompts
├── audio_service.py        168 lines — STT/TTS
├── image_service.py         91 lines — SD/ComfyUI image gen
├── skills.py                86 lines — SkillManager (prompt directives)
├── config.json                         — app config (url, model, hotkeys, whisper, tts, monitor)
├── skills.json                         — persisted skills + active_skill
├── history.json                        — persisted 100-item prompt/response history
├── diagnostic.py           158 lines — health check: imports, clipboard, Ollama, hotkeys
├── requirements.txt                    — PySide6 pynput pyautogui pyperclip pyttsx3 …
├── start.bat               ~70 lines — one-click launcher (dep check + ollama serve + pythonw)
├── stop.bat                            — clean shutdown via CIM Win32_Process
├── run.vbs                             — double-click hidden launch of start.bat
├── agent_logic/                        — AI-agent method specs (md + json schema)
│   ├── README.md                       — method overview & file contract (logic.md/json)
│   ├── rewrite_spec.md                 — Rewrite mode spec + bugfix 2026-09-24
│   ├── plan_spec.md                    — Plan mode: PART1 detailed plan + PART2 logic.md/json
│   ├── logic_template.md               — Markdown workflow template
│   └── workflow_template.json          — JSON Schema draft-07 for logic.json
├── templates/
│   ├── logic_template.md               — minimal md template
│   └── logic_template.json             — minimal json template
├── history.json, app_log.txt, __pycache__/, .git/, .gitignore, Ollama, lib commad install.txt
└── PROJECT_STRUCTURE.md    ← this file
```

---

## 3. Core Files — Details & Usage

### 3.1 `main.py` — System Tray Entry Point

| Field | Detail |
|---|---|
| **Purpose** | Single entry. Creates `QApplication`, loads config, starts services, builds tray, hotkeys, selection monitor. Runs `app.exec()` forever. |
| **Lines** | 529 |
| **Inside** | `load_config()` — reads `config.json` with fallback defaults <br>`create_tray_icon()` — draws purple rounded lightning pixmap <br>`is_auto_startup_enabled()` / `get_pythonw_executable()` / `set_auto_startup(enable)` — registry + Startup `.lnk` via PowerShell `WScript.Shell` <br>`get_selected_text()` — `pyperclip.paste()` <br>`build_tray_menu(window, popup, config)` — QMenu: Open Quick Bar, History, AI on Clipboard, Voice, Startup toggle (writes `config.json`), Clipboard monitor toggle, model badge, Exit <br>`HotkeyBridge(QObject)` — signals: `toggle_quick_bar_signal`, `process_selection_signal`, `voice_to_text_signal`, `text_selected_signal`, `text_copied_signal` <br>`SelectionMonitor` — `pynput mouse/keyboard` listeners: mouse drag `>12px` + `>0.2s` since typing → `Ctrl+C` → `pyautogui.hotkey` → emit `text_selected_signal`; `Ctrl+C` (`\x03`) → `_check_copy_action` emit `text_copied_signal`; `_is_internal_copying` flag avoids loop <br>`setup_hotkeys(bridge, config)` — `keyboard.GlobalHotKeys` from `config.hotkeys` <br>`main()` — Fusion style, first-run auto-startup, creates `OllamaService`, `AudioService`, `ImageService`, `HistoryManager`, `AIHelperWindow`, `NearbySuggestionPopup`, wires bridge signals with `0.6s` debounce, starts `SelectionMonitor`, `build_tray_menu`, thread `setup_hotkeys` |
| **Usage** | `python main.py` or `start.bat` (hidden `pythonw main.py`). `Ctrl+Alt+G/X/V`. Tray right-click for toggles. Auto-restart on boot if `auto_startup:true`. |
| **Deps** | `PySide6`, `pynput`, `pyautogui`, `pyperclip`, `winreg`, `ollama_service`, `audio_service`, `image_service`, `gui_overlay` |

---

### 3.2 `gui_overlay.py` — All UI

> Largest file. Two main widgets + helpers. Translucent frameless `Qt.Tool` windows.

#### 3.2.1 Helpers

| Component | Detail |
|---|---|
| `clean_think_text(text)` | Regex strips `<think>…</think>`/`<thought>` + 3-pass intro fluff (`Sure, Here is…`) + outro (`Hope this helps…`) |
| `ThinkFilter` | Streaming parser: `process_chunk` buffers partial tags (`<thi…`), toggles `in_think`, calls `on_thinking_state_change`. `flush()` |
| `HistoryLineEdit(QLineEdit)` | Up/Down navigates deduped `history_manager.history[].prompt`, preserves `draft_text` |
| `HistoryManager` | JSON `history.json` (100 max). `add_entry(action,prompt,response,model)` with `id=ms`, `search(query)` substring. |
| `HistoryDialog(QDialog)` | 580×520, search bar + Clear, scroll cards with badge+time+delete, prompt/response `QTextEdit` (selectable), Copy Prompt/Response buttons, `QTimer` reset. |
| `AddSkillDialog(QDialog)` | 400×240, name + prompt `QTextEdit`, Save/Cancel |
| `WorkerThread(QThread)` | `chunk_received(str)`, `finished`; runs `generator_func()` |

#### 3.2.2 `NearbySuggestionPopup(QWidget)` — Floating Bar Near Cursor

| Field | Detail |
|---|---|
| **Flags** | `WindowStaysOnTopHint|FramelessWindowHint|Tool` + `WA_TranslucentBackground`, draggable |
| **UI** | Card `#1a1a20` border `#4338ca`: header (model `QComboBox` + preview `Selected: "..."` 40 chars + ✕), chips row (Rewrite, Translate, Summary, Explain, Ask AI, Copy, Paste, Open), `ask_container` (HistoryLineEdit + Send), `output_view` (110px `QTextEdit` `#121216`), `status_label` |
| **Key Methods** | `refresh_model_dropdown()` — `ollama.get_available_models()` → `⚡ model` <br>`show_near_position(text,x,y,trigger_type)` — truncates, resets views, `adjustSize`→430w, positions `x+10,y+15` clamped to screen, `raise+activate` <br>`on_chip_clicked(action)` — `expand`→`expand_requested`, `copy`→clipboard, `paste`→clipboard text→show ask, `ask`→show ask, else `run_ai_action` <br>`submit_ask()` — `selected_text -> prompt` + `You are helpful…` → `_execute_streaming` <br>`_execute_streaming` → `ThinkFilter` + `WorkerThread(ollama.stream_generate)` <br>`_on_finished` → `flush` → `clean_think_text` → `history.add_entry` → `✓ Ready` |
| **Usage** | Triggered by `SelectionMonitor` or `Ctrl+Alt+X`. One-click AI without opening full window. |

#### 3.2.3 `AIHelperWindow(QWidget)` — Quick Bar (Main)

| Field | Detail |
|---|---|
| **Size/Style** | 640×470, card `#1e1e24` radius12, draggable |
| **Top Bar** | Title + Model `QComboBox` + Skill `QComboBox` + History button + ✕ |
| **Status+Ctx** | `status_label` (model/thinking) + `ctx_label` (📋 Selected N chars + 200-char preview in `#272730`) |
| **Actions Row1** | `✍️ Rewrite` (grammar polish, skill-bypass, temp0.2) <br>`✨ Expand` <br>`📋 Plan` (complete plan + logic.md/json, skill-bypass) <br>`📖 Explain` <br>`🌐 Translate` + `Lang:` `QComboBox` (10 langs) <br>`📝 Summarize` <br>Each `25px`, hover `#3f3f4e` |
| **Media Row** | `🎙 Voice` (checkable → `audio.start_recording/stop_and_transcribe`) + `🔊 Read Aloud` (`audio.speak`) + `🖼 Image` (`image.generate_image`) |
| **Output** | `output_view` `QTextEdit` `#141418` |
| **Bottom Bar** | `input_field` (HistoryLineEdit, placeholder `Type… Up/Down`) + `Details`/`📋 Copy`/`✂️ Clear` |
| **Writing Assist (NEW)** | `writing_suggest_frame` `#1a1a2e` border `#4338ca`: `✨ suggestion` label (selectable) + `✔ Apply` (replaces input) + `📋` copy + `✕` dismiss. Debounce `QTimer 650ms` → `_request_writing_suggestion()` → `ollama.get_action_prompt("writing_assist", text)` → `temperature 0.2` → `ThinkFilter` stream → `_on_writing_finished` hides if identical, truncates 180 chars. Skips when skill `Code Only`/`JSON` or prefix `/plan /code /json`. |
| **Completer** | `QCompleter` for `/rewrite /plan /summarize /json /tanglish /code …` + phrases; shown only when text starts `/` |
| **Key Methods** | `refresh_model_dropdown`, `_on_model_changed`, `refresh_skill_dropdown`, `_on_skill_selected` (Add Custom Skill), `_detect_clipboard`, `show_centered/near_cursor/selection_popup`, `execute_action(action)` — resolves `selected_text||input`, `lang_combo`, `get_action_prompt` → `_run_action` <br>`_run_action(user_input, system_prompt)` — terminates old worker, **bypasses skill** if `_current_action_name in (rewrite,plan)` else `skill_prompt + system_prompt` → `WorkerThread(stream_generate)` → `_append_chunk` (ThinkFilter + autoscroll) → `_on_worker_finished` (flush, clean, history) <br>`toggle_voice_input`, `read_aloud`, `generate_image`, `on_manual_action`, `process_clipboard_selection` (rewrite by default) <br>`_request_writing_suggestion` family (see above) |
| **Usage** | `Ctrl+Alt+G` center, type prompt + Enter or click action chips. Drag anywhere. `Esc` hides Nearby, Quick Bar hides via ✕/tray. |

---

### 3.3 `ollama_service.py` — LLM Client

| Field | Detail |
|---|---|
| **Class** | `OllamaService(base_url, default_model, keep_alive)` |
| **Constants** | `STRICT_SUFFIX` — `Return ONLY final output. DO NOT…` <br>`_ACTIONS` dict: `rewrite` (GRAMMAR REWRITE ENGINE + few-shot), `enhance`, `plan` (PART1 detailed plan + PART2 logic.md/json), `explain`, `translate`, `summarize`, `details`, `writing_assist` (NEW: Grammarly short result, few-shot `pleases fidn…`) |
| **Model Resolve** | `_resolve_model()` — `GET /api/tags` → fallback to first non-embed |
| **Streaming** | `stream_generate(prompt, system_prompt, model, temperature)` — auto `0.2` if `GRAMMAR REWRITE ENGINE`/`WRITING ASSISTANT` in sys_prompt else `0.3` if `SHORT RESULT` else `0.6`; `options {temperature, top_p, repeat_penalty:1.05}`; `POST /api/generate` stream JSON lines → `yield response`; 45s timeout; error yield |
| **Prompt Builder** | `get_action_prompt(action_type, text, target_lang)` → `(system_prompt, user_text)`: <br>• `translate` → `Translate into {lang}` <br>• `enhance` → richer vocab <br>• `rewrite` → `GRAMMAR REWRITE` + `OVERRIDE` + `OUTPUT ONLY polished` + wrapper `<<<DRAFT_START>>>` <br>• `plan` → `PART1 7 sections` + `PART2 logic.md/json fences` + `<<<Objective>>>` <br>• `writing_assist` → `WRITING ASSISTANT SHORT RESULT` + `<<<TEXT_START>>>` <br>• else → `base_p + STRICT_SUFFIX (+SHORT RESULT conditional for generic)` |
| **Usage** | `svc.stream_generate(prompt, system_prompt=sys_prompt)` in GUI workers; `get_action_prompt` centralizes all prompt engineering; `set_model/get_model_name` for dropdown |

---

### 3.4 `audio_service.py` — Voice

| Field | Detail |
|---|---|
| **Class** | `AudioService(whisper_size="base")` |
| **Inside** | `speak(text)` — threaded: detects Tamil `0x0B80-0x0BFF` → Google TTS chunk 150×3 via `translate.google.com/translate_tts` → `MediaPlayer` PowerShell; else `pyttsx3.init(rate=TTS_RATE)` <br>`start_recording()` — `sounddevice InputStream 16k mono int16` callback appends frames <br>`stop_and_transcribe()` — `numpy.concatenate` → temp wav → lazy `WhisperModel(whisper_size,cpu,int8)` → `transcribe(beam5,vad_filter, initial_prompt)` → join segments <br>`stop_recording()` — flag off |
| **Usage** | `voice_btn` toggles; `Read Aloud` calls `speak(output)` |

---

### 3.5 `image_service.py` — Image Gen

| Field | Detail |
|---|---|
| **Class** | `ImageService(api_url)` default `127.0.0.1:7860/sdapi/v1/txt2img` |
| **Inside** | `generate_image(prompt)` — POST `{prompt,steps20,512x512,cfg7}` → `images[0]` base64 → temp png path; fallback ComfyUI `api/generate` <br>`get_api_status()` — `GET sd-models` or `system_stats` |
| **Usage** | Quick Bar `🖼 Image` button → `_show_result` displays saved path |

---

### 3.6 `skills.py` / `skills.json`

| File | Detail |
|---|---|
| `skills.py` | `SkillManager(filepath=skills.json)`: `DEFAULT_SKILLS` 4 (Direct Answer, JSON Only, Tanglish, Code Only), `load_skills()`/`save_skills()`, `get_skill_names()`, `get_active_skill_prompt()` (empty if `None (Default)`), `add_skill`, `set_active_skill` |
| `skills.json` | Persisted `{active_skill, skills[]}` — currently 6 skills (4 defaults + Stock/Index Forecast ×2). Edited via `AIHelperWindow` skill dropdown + `AddSkillDialog`. Bypassed for `rewrite`/`plan`/`writing_assist` to avoid conflict. |
| **Usage** | Dropdown in Quick Bar injects `skill_prompt + system_prompt` in `_run_action` except writing exceptions |

---

### 3.7 `config.json`

```json
{
  "ollama_url": "http://localhost:11434",
  "default_model": "gemma3:1b-it-qat",
  "keep_alive": "2m",
  "hotkeys": {"toggle_quick_bar":"<ctrl>+<alt>+g", "process_selection":"<ctrl>+<alt>+x", "voice_to_text":"<ctrl>+<alt>+v"},
  "sd_api_url": "http://127.0.0.1:7860/sdapi/v1/txt2img",
  "whisper_model_size": "base",
  "tts_rate": 180,
  "enable_clipboard_monitor": true,
  "clipboard_poll_interval_ms": 500,
  "auto_startup": true,
  "first_run_complete": true
}
```
Editable live via tray toggles (writes back). `load_config()` fallback if missing.

---

### 3.8 `diagnostic.py` — Health Check

Steps: 1) import `PySide6 pynput pyautogui pyperclip pyttsx3 sounddevice numpy PIL` + `ollama_service/audio_service/image_service/gui_overlay` 2) clipboard round-trip marker `WINAIHELPER_MARKER_…` 3) `GET localhost:11434/api/tags` list models 4) hotkey note. Run `python diagnostic.py`.

---

### 3.9 `requirements.txt`

```
PySide6
pynput
pyautogui
pyperclip
pyttsx3
sounddevice
numpy
faster-whisper
Pillow
```

---

### 3.10 Launchers

| File | Purpose |
|---|---|
| `start.bat` | Finds `python.exe/pythonw.exe` (hermes venv or `LOCALAPPDATA\Python314`), installs `requirements.txt` if `PySide6` missing, starts `ollama serve` if needed, runs `pythonw main.py` detached (0 hidden), self-closes |
| `stop.bat` | `Get-CimInstance Win32_Process where Name~python* and CommandLine~*main.py* | Stop-Process -Force` |
| `run.vbs` | `WScript.Shell.Run "cmd /c start.bat",0,False` — double-click hidden launch |
| `.gitignore` | `__pycache__/, *.pyc, venv/, .env` etc (49 bytes) |

---

### 3.11 `agent_logic/` — AI-Agent Method Specs

| File | Content |
|---|---|
| `README.md` | Core principle `Never output raw code alone. Every script wrapped as executable logic.` Contract: `logic.md` (Objective, Deliverables, File Tree, Execution Order, Steps with input/output/tool/validation + code fences) + `logic.json` (`{meta,workflow[],files[],env,acceptance_criteria[]}`) |
| `rewrite_spec.md` | Bugfix note 2026-09-24 (ambiguous prompt + skill override + temp0.6 → GRAMMAR ENGINE + `<<<DRAFT_START>>>` + skill bypass + temp0.2), input/output contract, few-shot, integration via `gui_overlay:1001` |
| `plan_spec.md` | 7-section PART1 table + PART2 `logic.md` template + `logic.json` schema reference + validation checklist; example `Build Python script to scrape NSE` |
| `workflow_template.json` | JSON Schema draft-07: `meta{objective,version}`, `workflow[{step,id,action,input,output,tool,depends_on,priority,code_block,validation}]`, `files[{path,purpose,template}]`, `env`, `acceptance_criteria[]` + full example |
| `logic_template.md` | `# Workflow: <TITLE>` with Objective, Deliverables, File Tree, Execution Order, Step1/2/3 examples |

---

### 3.12 `templates/`

| File | Purpose |
|---|---|
| `logic_template.json` | Minimal `{"meta":{objective}, "workflow":[setup], "files":[main.py], "env":{}}` |
| `logic_template.md` | Minimal `{{TITLE}} {{OBJECTIVE}} {{TREE}}` placeholder |

---

### 3.13 Data Files

| File | Detail |
|---|---|
| `history.json` | Array 100 entries `{id,timestamp,action,prompt,response,model}` — written by both `AIHelperWindow` and `NearbySuggestionPopup` on `_on_finished` |
| `app_log.txt` | Fatal traceback on `main() except` |

---

## 4. Data & Control Flow

```
[Mouse drag / Ctrl+C] → SelectionMonitor (pynput) → HotkeyBridge signals → NearbySuggestionPopup.show_near_position
       ↘ Ctrl+Alt+G/X/V → GlobalHotKeys → HotkeyBridge → AIHelperWindow.show_centered / process_selection / voice
Typing in QuickBar input → _on_input_text_changed → 650ms Timer → writing_assist (Ollama, temp0.2, no skill) → suggestion bar → Apply/Copy
Action click (Rewrite/Plan/…) → get_action_prompt → _run_action → WorkerThread(stream_generate) → ThinkFilter → output_view → clean_think_text → history.json
Tray menu → toggles write config.json + startup registry/lnk
```

---

## 5. How to Use

| Task | Command |
|---|---|
| Start hidden | `start.bat` or `run.vbs` |
| Stop | `stop.bat` |
| Manual run | `python main.py` |
| Diagnose | `python diagnostic.py` |
| Change model | QuickBar/Nearby dropdown `⚡ model` |
| Add skill | Skill dropdown → `➕ Add Custom Skill…` |
| Toggle monitor | Tray → `📎 Clipboard Monitor` |

---

## 6. Extension Points

- Add new `_ACTIONS` in `ollama_service.py` and chip in `gui_overlay.py:action_chips` + `row_btns`.
- Writing assist threshold `len>=4` and timer `650ms` tunable in `gui_overlay.py`.
- `workflow_template.json` schema is validation target for any `plan` output.

---

*This file was auto-generated for complete project view. For usage see `README.md` Quick Bar / Nearby Bar / Tray sections.*
