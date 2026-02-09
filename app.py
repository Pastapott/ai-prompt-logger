import os
import json
from datetime import datetime, timezone
import google.generativeai as genai
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

app = Flask(__name__)

LOG_FILE = os.path.join(os.path.dirname(__file__), "prompt_logs.jsonl")


def append_log(record: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_logs(limit: int = 50) -> list[dict]:
    if not os.path.exists(LOG_FILE):
        return []
    rows = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # skip bad lines
                pass
    return rows[-limit:]


def stub_ai_reply(prompt: str) -> str:
    # Free, deterministic "AI-like" response for demos with no API cost.
    prompt = prompt.strip()
    if not prompt:
        return "Please enter a prompt."
    return (
        "Stub AI reply (no API used):\n\n"
        f"- I received your prompt ({min(len(prompt), 80)} chars preview): "
        f"“{prompt[:80]}{'...' if len(prompt) > 80 else ''}”\n"
        "- In real mode, this would call the LLM API and return its answer."
    )

def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    if not api_key:
        return "ERROR: GEMINI_API_KEY is not set."

    genai.configure(api_key=api_key)

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"ERROR calling Gemini API: {str(e)}"


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/logs")
def api_logs():
    return jsonify({"logs": read_logs(limit=50)})


@app.post("/api/generate")
def api_generate():
    body = request.get_json(force=True, silent=True) or {}
    prompt = str(body.get("prompt", "")).strip()

    use_real_ai = os.getenv("USE_REAL_AI", "false").lower() == "true"

    if use_real_ai:
        reply = call_gemini(prompt)
        mode = "real-gemini"
    else:
        reply = stub_ai_reply(prompt)
        mode = "stub"

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "prompt": prompt,
        "reply": reply,
        "env": os.getenv("APP_ENV", "dev"),
    }
    append_log(record)

    return jsonify({"reply": reply, "mode": mode, "record": record})


if __name__ == "__main__":
    # For local dev; in production you’d run with gunicorn, etc.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)