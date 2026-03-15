import os
import requests


class ImagenClient:
    def __init__(self, api_key, model, timeout):
        self.api_key = (api_key or "").strip()
        self.model = (model or "").strip()
        self.timeout = timeout

    @staticmethod
    def from_env(timeout=60):
        api_key = os.getenv("GOOGLE_API_KEY", "")
        model = os.getenv("IMAGEN_MODEL", "imagen-3.0-generate-002")
        return ImagenClient(api_key, model, timeout)

    @staticmethod
    def _debug_enabled():
        return (os.getenv("FLASK_DEBUG", "") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @staticmethod
    def _error_info(data):
        status_txt = ""
        message = ""
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                status_txt = (err.get("status") or "").upper()
                message = err.get("message") or ""
        return status_txt, message

    def _debug_upstream_error(self, status_code, data):
        if not self._debug_enabled():
            return
        data_keys = list(data.keys()) if isinstance(data, dict) else []
        _, message = self._error_info(data)
        error_status = ""
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                error_status = err.get("status") or ""
        print(
            "[IMAGEN_DEBUG] status_code={0} error.status={1} error.message={2} data.keys={3}".format(
                status_code,
                error_status,
                message,
                data_keys,
            )
        )

    def list_models(self):
        if not self.api_key:
            return {
                "ok": False,
                "error": "Missing GOOGLE_API_KEY in backend environment.",
                "code": "MISSING_KEY",
                "http_status": 500,
            }

        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {"x-goog-api-key": self.api_key}

        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout)
        except requests.exceptions.Timeout:
            return {"ok": False, "error": "Request timed out.", "code": "TIMEOUT", "http_status": 504}
        except requests.exceptions.RequestException:
            return {"ok": False, "error": "Network error while requesting models.", "code": "NETWORK", "http_status": 502}

        try:
            data = resp.json()
        except ValueError:
            return {"ok": False, "error": "Invalid upstream response JSON.", "code": "UPSTREAM", "http_status": 502}

        if resp.status_code != 200:
            self._debug_upstream_error(resp.status_code, data)
            return self._map_error(resp.status_code, data)

        return {"ok": True, "http_status": 200, "data": data}

    def generate(self, prompt):

        if not self.api_key:
            return {
                "ok": False,
                "error": "Backend is missing GOOGLE_API_KEY.",
                "code": "MISSING_KEY",
                "http_status": 500,
            }

        model = self.model
        if model.startswith("models/"):
            model = model[7:]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1},
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.exceptions.Timeout:
            return {"ok": False, "error": "Request timed out. Try again later.", "code": "TIMEOUT", "http_status": 504}
        except requests.exceptions.RequestException:
            return {"ok": False, "error": "Network error. Please retry.", "code": "NETWORK", "http_status": 502}

        try:
            data = resp.json()
        except ValueError:
            data = None

        if resp.status_code != 200:
            self._debug_upstream_error(resp.status_code, data)
            return self._map_error(resp.status_code, data)

        image_base64, image_url, mime_type = self._extract_image(data)
        if not image_base64 and not image_url:
            return {
                "ok": False,
                "error": "Upstream response does not contain image data.",
                "code": "NO_IMAGE",
                "http_status": 502,
            }

        return {
            "ok": True,
            "image_base64": image_base64,
            "image_url": image_url,
            "mime_type": mime_type or "image/png",
        }

    def _extract_image(self, data):
        if not isinstance(data, dict):
            return "", "", "image/png"

        candidates = []
        if isinstance(data.get("predictions"), list):
            candidates = data["predictions"]
        elif isinstance(data.get("generatedImages"), list):
            candidates = data["generatedImages"]
        elif isinstance(data.get("images"), list):
            candidates = data["images"]

        if not candidates:
            return "", "", "image/png"

        first = candidates[0] if isinstance(candidates[0], dict) else {}
        image_base64 = (
            first.get("bytesBase64Encoded")
            or first.get("imageBytes")
            or first.get("b64")
            or first.get("base64")
            or ""
        )
        image_url = (
            first.get("imageUri")
            or first.get("imageUrl")
            or first.get("url")
            or ""
        )
        mime_type = first.get("mimeType") or "image/png"
        return image_base64, image_url, mime_type

    def _map_error(self, http_status, data):
        status_txt = ""
        message = f"Upstream API failed with HTTP {http_status}."
        parsed_status, parsed_message = self._error_info(data)
        if parsed_status:
            status_txt = parsed_status
        if parsed_message:
            message = parsed_message

        if http_status == 429 or status_txt == "RESOURCE_EXHAUSTED":
            return {
                "ok": False,
                "error": "Quota exceeded or too many requests. Please retry later.",
                "code": "QUOTA",
                "http_status": 429,
            }

        if http_status in (401, 403) or status_txt == "PERMISSION_DENIED":
            return {
                "ok": False,
                "error": "Authentication failed. Check API key and permissions.",
                "code": "AUTH",
                "http_status": 403,
            }

        if http_status == 400 or status_txt == "INVALID_ARGUMENT":
            return {
                "ok": False,
                "error": message,
                "code": "BAD_REQUEST",
                "http_status": 400,
            }

        return {
            "ok": False,
            "error": message,
            "code": "UPSTREAM",
            "http_status": http_status,
        }
