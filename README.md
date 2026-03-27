<img width="554" height="432" alt="AIGen" src="https://github.com/user-attachments/assets/f905ed8a-5be9-4c2d-bd5c-2bc9b05c1b11" />


# 1 Flask Imagen Demo

A small Flask backend + web UI for image generation using Google Imagen API.

## 1.1 Project Structure

```text
.
├── app.py                 # app factory, config loading, blueprint registration
├── routes/
│   └── main.py            # GET / page route | POST /generate API route
├── services/
│   └── imagen_client.py   # Imagen API client/service layer
├── utils/
│   └── responses.py       # unified API response helpers
├── templates/
│   └── index.html         # HTML templates
├── static/
│   ├── css/
│   └── js/
├── requirements.txt
└── .env.example
```


## 1.2 Requirements

- Python 3.10+
- A valid Google API key with Imagen access

## 1.3 Install

```bash
python -m venv venv

(windows powershell)
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## 1.4 Environment Variables

Copy `.env.example` to `.env` and fill values:

- GOOGLE_API_KEY: your API key
- IMAGEN_MODEL: model name, e.g. `models/imagen-4.0-generate-001`
- IMAGEN_TIMEOUT: request timeout in seconds (default `60`)
- MAX_PROMPT_LEN: prompt max length (default `500`)
- FLASK_DEBUG: `true/false`

## 1.5Run the app

```bash
python app.py
```

Open `http://127.0.0.1:5000`.



# 2 API Integration Documentation
## 2.1 Endpoint
GET /: Returns the frontend page.

POST /generate: Generates an image using Google Imagen.

Accepts:
JSON body:
{
  "prompt": "a futuristic cyberpunk city at night"
}
Or form submission:
prompt=...

## 2.2 Success Response (HTTP 200)
{
  "success": true,
  "image_base64": "<base64-optional>",
  "image_url": "<url-optional>",
  "mime_type": "image/png"
}

Frontend renders the image using either image_url or Base64 with mime_type

## 2.3 Error Response
{
  "success": false,
  "error": "Human-readable message",
  "code": "ERROR_CODE"
}
All failures use the unified structure above.

# 3.Error Handling Strategy / Backend Design

## 3.1 Input Validation (Backend)
Prompt is required and trimmed
Prompt length must be 1..MAX_PROMPT_LEN
Invalid JSON → rejected
Unsupported content type → rejected

## 3.2 Upstream Error Mapping
Google Imagen API errors are mapped into structured codes:
- `INVALID_PROMPT`: prompt missing or empty
- `PROMPT_TOO_LONG`: prompt exceeds `MAX_PROMPT_LEN`
- `INVALID_JSON`: invalid JSON body / unsupported content type
- `MISSING_KEY`: backend key missing
- `TIMEOUT`: upstream timeout
- `NETWORK`: network error
- `QUOTA`: quota/rate limit reached
- `BAD_REQUEST`: invalid upstream arguments
- `AUTH`: permission/key issue
- `UPSTREAM`: other upstream failures

## 3.3 Backend Flow
Frontend sends POST /generate
Backend validates prompt
imagen_client.py constructs and sends POST request to Google Imagen
On success → returns unified ok(...)
On failure → returns unified fail(...)
Frontend reads success/error/code and updates UI

## 3.4 Security
API key is stored only in .env
API key is never exposed to frontend
Sensitive values are not logged
Full prompt text is not logged
Only prompt length is logged

## 3.5 Logging
Each /generate request logs:
- prompt length
- latency (ms)
- success/failure
- failure code (if any)

No API key or full prompt content is logged.
