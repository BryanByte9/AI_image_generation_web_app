function $(id) {
  return document.getElementById(id);
}

function maxPromptLen() {
  const value = document.body?.dataset?.maxPromptLen;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 500;
}

function asImageSrc(value, mime_type) {
  if (!value || typeof value !== "string") return "";
  if (value.startsWith("data:image/")) return value;
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  return `data:${mime_type || "image/png"};base64,${value}`;
}

function pickImageData(data) {
  if (!data || typeof data !== "object") {
    return { value: "", mime_type: "image/png" };
  }
  const image_url = typeof data.image_url === "string" ? data.image_url : "";
  const image_base64 = typeof data.image_base64 === "string" ? data.image_base64 : "";
  const mime_type = typeof data.mime_type === "string" ? data.mime_type : "image/png";
  return { value: image_url || image_base64, mime_type };
}

function setLoading(isLoading) {
  const btn = $("generateBtn");
  const btnText = $("btnText");
  const spinner = $("spinner");
  const statusText = $("statusText");

  btn.disabled = isLoading;
  if (isLoading) {
    btnText.textContent = "Generating...";
    spinner.classList.remove("hidden");
    statusText.textContent = "Generating...";
  } else {
    btnText.textContent = "Generate";
    spinner.classList.add("hidden");
    statusText.textContent = "Ready";
  }
}

function setError(msg) {
  const el = $("errorText");
  if (!msg) {
    el.textContent = "";
    el.classList.add("hidden");
    return;
  }
  el.textContent = msg;
  el.classList.remove("hidden");
}

function updatePromptGuide() {
  const promptEl = $("prompt");
  const limit = maxPromptLen();
  const length = (promptEl.value || "").length;
  const counterEl = $("promptCounter");
  const limitMsg = `Prompt is too long (max ${limit} characters).`;

  if (counterEl) {
    counterEl.textContent = `${length}/${limit}`;
  }

  if (length >= limit) {
    setError(limitMsg);
  } else if ($("errorText").textContent === limitMsg) {
    setError("");
  }
}

function showImage(src) {
  const img = $("resultImage");
  const ph = $("placeholder");

  if (!src) {
    img.src = "";
    img.classList.add("hidden");
    ph.classList.remove("hidden");
    return;
  }

  img.src = src;
  img.classList.remove("hidden");
  ph.classList.add("hidden");
}

async function generate() {
  const promptEl = $("prompt");
  const prompt = (promptEl.value || "").trim();
  const limit = maxPromptLen();
  const limitMsg = `Prompt is too long (max ${limit} characters).`;

  if ($("errorText").textContent !== limitMsg) {
    setError("");
  }

  if (!prompt) {
    setError("Please enter a prompt.");
    return;
  }

  if (prompt.length > limit) {
    setError(`Prompt is too long (max ${limit} characters).`);
    return;
  }

  setLoading(true);

  try {
    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt })
    });

    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error(`Invalid server response (${res.status}).`);
    }

    if (!data || typeof data !== "object" || typeof data.success !== "boolean") {
      throw new Error(`Invalid server response (${res.status}).`);
    }

    if (!data.success) {
      const baseMsg = typeof data.error === "string" ? data.error : `Request failed (${res.status})`;
      const msg = data.code ? `${baseMsg} (${data.code})` : baseMsg;
      throw new Error(msg);
    }

    if (!res.ok) {
      throw new Error(`Request failed (${res.status})`);
    }

    const picked = pickImageData(data);
    const src = asImageSrc(picked.value, picked.mime_type);

    if (!src) {
      throw new Error("No image returned from server.");
    }

    showImage(src);
  } catch (err) {
    showImage("");
    setError(err && err.message ? err.message : "Something went wrong.");
  } finally {
    setLoading(false);
  }
}

function init() {
  const btn = $("generateBtn");
  const promptEl = $("prompt");
  const limit = maxPromptLen();

  promptEl.maxLength = limit;

  btn.addEventListener("click", generate);
  promptEl.addEventListener("input", updatePromptGuide);

  promptEl.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      generate();
    }
  });

  updatePromptGuide();
}

document.addEventListener("DOMContentLoaded", init);
