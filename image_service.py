import json
import base64
import urllib.request
import os
import tempfile


class ImageService:
    """Local Stable Diffusion / ComfyUI image generation via API."""

    def __init__(self, api_url: str = "http://127.0.0.1:7860/sdapi/v1/txt2img"):
        self.api_url = api_url.rstrip("/")
        # Optional: Stable Diffusion WebUI ControlNet or other extensions endpoint

    def generate_image(self, prompt: str) -> str | None:
        """Generate an image from text prompt. Returns path to saved PNG."""
        if not prompt.strip():
            return None

        payload = {
            "prompt": prompt,
            "steps": 20,
            "width": 512,
            "height": 512,
            "cfg_scale": 7.0
        }

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if "images" in result and len(result["images"]) > 0:
                    img_data = base64.b64decode(result["images"][0])
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp.write(img_data)
                    tmp.close()
                    return tmp.name
        except Exception as e:
            pass

        # Fallback: try ComfyUI API if available
        comfy_url = self.api_url.replace("sdapi/v1/txt2img", "api/generate")
        if comfy_url != self.api_url:
            payload_c = {
                "prompt": {"text": prompt},
                "client_id": ""
            }
            try:
                req = urllib.request.Request(
                    comfy_url,
                    data=json.dumps(payload_c).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result_c = json.loads(resp.read().decode("utf-8"))
                    for item in result_c.get("outputs", []):
                        b64img = item.get("images", [None])[0]
                        if b64img:
                            img_data = base64.b64decode(b64img)
                            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                            tmp.write(img_data)
                            tmp.close()
                            return tmp.name
            except Exception:
                pass

        return None

    def get_api_status(self) -> bool:
        """Check if image generation service is reachable."""
        try:
            req = urllib.request.Request(
                f"{self.api_url}/sdapi/v1/sd-models",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            return True
        except Exception:
            # Try ComfyUI status
            try:
                req = urllib.request.Request(f"{self.api_url}/system_stats", headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read()
                return True
            except Exception:
                return False