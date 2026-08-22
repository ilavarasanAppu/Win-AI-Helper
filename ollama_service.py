import json
import urllib.request
from typing import Callable, Generator


class OllamaService:
    """Ollama API client with lazy model management and streaming."""

    # ── action prompt definitions ──────────────────────────────
    _ACTIONS = {
        "rewrite": (
            "You are an expert editor. Rewrite and polish the provided text to improve clarity, tone, "
            "and grammar while preserving its original meaning. Return only the revised text. Do not output <think> tags or reasoning steps."
        ),
        "enhance": (
            "Enhance and expand the following text with richer vocabulary, better structure, and more detail. "
            "Preserve the core idea but make it professional and compelling. Return the enhanced text. Do not output <think> tags or reasoning steps."
        ),
        "plan": (
            "You are an expert planner. Break down the provided objective or context into a clear, actionable, "
            "structured step-by-step plan with priorities and milestones. Do not output <think> tags or reasoning steps."
        ),
        "explain": (
            "You are a concise tutor. Explain the meaning, concept, or logic of the provided text clearly "
            "with simple terms and concise examples. Do not output <think> tags or reasoning steps."
        ),
        "translate": (
            "Translate the following text accurately into natural English (or Tamil if input is English). "
            "Preserve nuance and tone. Return only the translation. Do not output <think> tags or reasoning steps."
        ),
        "summarize": (
            "Summarize the key points of the provided text into clear, concise bullet points. Do not output <think> tags or reasoning steps."
        ),
        "details": (
            "Provide detailed information, additional context, or deeper analysis on the following topic. "
            "Be thorough and structured. Do not output <think> tags or reasoning steps."
        ),
    }

    def __init__(self, base_url: str = "http://localhost:11434",
                 default_model: str = "lfm2.5-thinking:latest",
                 keep_alive: str = "2m"):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.keep_alive = keep_alive
        self._selected_model = None
        self._resolve_model()

    def get_available_models(self) -> list[str]:
        """Fetch list of installed models from Ollama."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"Content-Type": "application/json"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                return [m.get("name") for m in data if isinstance(m, dict)]
            elif isinstance(data, dict):
                models = data.get("models", [])
                return [m.get("name") for m in models if isinstance(m, dict)]
        except Exception:
            pass
        return []

    def _resolve_model(self):
        """Ensure default_model exists in Ollama; fallback to an available model if not."""
        available = self.get_available_models()
        if not available:
            self._selected_model = self.default_model
            return

        # Check exact or prefix match
        if any(m == self.default_model or m.startswith(self.default_model.split(":")[0]) for m in available):
            self._selected_model = self.default_model
        else:
            # Fallback to first non-embed model or first available model
            valid = [m for m in available if "embed" not in m.lower() and "bge" not in m.lower()]
            fallback = valid[0] if valid else available[0]
            print(f"⚠️  Configured model '{self.default_model}' not found in Ollama. Falling back to '{fallback}'.")
            self.default_model = fallback
            self._selected_model = fallback

    def ensure_model_loaded(self, model_name: str | None = None):
        """Set active model name (Ollama loads lazily on request)."""
        if not model_name:
            model_name = self.default_model
        self._selected_model = model_name

    def stream_generate(self, prompt: str, system_prompt: str = "",
                        model: str | None = None) -> Generator[str, None, None]:
        """Stream a chat-style generation from Ollama. Yields response chunks."""
        selected_model = model or self.default_model
        self.ensure_model_loaded(selected_model)

        payload = {
            "model": selected_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": 0.6,
                "top_p": 0.9
            }
        }

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                for line in response:
                    if not line:
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    resp_text = chunk.get("response", "")
                    if resp_text:
                        yield resp_text
                    if chunk.get("done", False):
                        break
        except Exception as e:
            yield f"\n[Error connecting to Ollama: {str(e)}. Ensure 'ollama serve' is running and model '{selected_model}' is available.]"

    def get_action_prompt(self, action_type: str, text: str, target_lang: str = "Tamil") -> tuple[str, str]:
        """Return (system_prompt, user_text) for the given action."""
        if action_type == "translate":
            sys_prompt = (
                f"Translate the following text accurately into natural {target_lang}. "
                "Preserve nuance and tone. Return only the translation. Do not output <think> tags or reasoning steps."
            )
        elif action_type in ("expand", "enhance"):
            sys_prompt = (
                "Enhance and expand the following text with richer vocabulary, better structure, and more detail. "
                "Preserve the core idea but make it professional and compelling. Return only the expanded text. Do not output <think> tags or reasoning steps."
            )
        else:
            sys_prompt = self._ACTIONS.get(action_type, "You are a helpful and concise Windows desktop assistant.")
        return sys_prompt, text

    def get_model_name(self) -> str:
        return self._selected_model or self.default_model

    def set_model(self, model_name: str):
        """Dynamically switch active model."""
        if model_name:
            self.default_model = model_name
            self._selected_model = model_name