def ok(data=None):
    payload = {"success": True}
    if isinstance(data, dict):
        payload.update(data)
    return payload


def ok_image(image_b64=None, image_url=None, mime_type=None):
    payload = ok()
    if image_b64:
        payload["image"] = image_b64
    if image_url:
        payload["imageUrl"] = image_url
    if mime_type:
        payload["mimeType"] = mime_type
    return payload

def fail(msg, code=None):
    payload = {"success": False, "error": msg}
    if code:
        payload["code"] = code
    return payload
