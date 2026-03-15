import time
from flask import Blueprint, request, jsonify, current_app

from services.imagen_client import ImagenClient
from utils.responses import ok, fail

api_bp = Blueprint("api", __name__)


def _extract_prompt():
    if request.is_json:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return "", True
        return data.get("prompt") or "", False

    if request.form:
        return request.form.get("prompt") or "", False

    return "", True


@api_bp.post("/generate")
def generate():
    start = time.time()
    prompt_raw, invalid_body = _extract_prompt()
    if invalid_body:
        return jsonify(fail("Invalid JSON body.", code="INVALID_JSON")), 400

    prompt = prompt_raw.strip()

    max_len = current_app.config.get("MAX_PROMPT_LEN", 500)

    if not prompt:
        return jsonify(fail("Prompt is required.", code="INVALID_PROMPT")), 400

    if len(prompt) > max_len:
        return jsonify(
            fail(
                f"Prompt too long. Max {max_len} characters.",
                code="PROMPT_TOO_LONG",
            )
        ), 400

    client = ImagenClient.from_env(timeout=current_app.config.get("IMAGEN_TIMEOUT", 60))
    result = client.generate(prompt)

    elapsed_ms = int((time.time() - start) * 1000)

    if not result.get("ok"):
        http_status = result.get("http_status") or 500
        code = result.get("code") or "GENERATION_FAILED"
        err = result.get("error") or "Image generation failed."
        current_app.logger.warning(
            "generate failed prompt_len=%s cost_ms=%s code=%s http_status=%s error=%s",
            len(prompt),
            elapsed_ms,
            code,
            http_status,
            err,
        )
        return jsonify(fail(err, code)), http_status

    current_app.logger.info(
        "generate success prompt_len=%s cost_ms=%s",
        len(prompt),
        elapsed_ms,
    )

    return jsonify(
        ok(
            {
                "image_base64": result.get("image_base64"),
                "image_url": result.get("image_url"),
                "mime_type": result.get("mime_type") or "image/png",
            }
        )
    ), 200


@api_bp.get("/models")
def models():
    client = ImagenClient.from_env(timeout=current_app.config.get("IMAGEN_TIMEOUT", 60))
    return jsonify(client.list_models())
