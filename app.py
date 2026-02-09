import os
import json
from datetime import datetime, timezone
import subprocess

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

LOG_FILE = "prompt_logs.jsonl"

APP_ENV = os.getenv("APP_ENV", "dev")
USE_REAL_AI = os.getenv("USE_REAL_AI", "false").lower() == "true"

# Build / version info
def get_version():
    if os.getenv("BUILD_VERSION"):
        return os.getenv("BUILD_VERSION")
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "local-dev"

BUILD_VERSION = get_version()

# ---------------- AI ----------------

def stub_ai(prompt: str) -> str:
    return f"(stub mode)\n\nPrompt received:\n{prompt}"

def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-pro")

    if not api_key:
        return "ERROR: GEMINI_API_KEY not set"

    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini error: {e}"

# ---------------- Logs ----------------

def read_logs(limit=200):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    logs = [json.loads(l) for l in lines if l.strip()]
    return logs[-limit:]

def write_log(entry: dict):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

# ---------------- Routes ----------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        env=APP_ENV,
        version=BUILD_VERSION
    )

@app.route("/prompts")
def prompts():
    logs = list(reversed(read_logs()))
    return render_template(
        "prompts.html",
        logs=logs,
        env=APP_ENV,
        version=BUILD_VERSION
    )

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if USE_REAL_AI:
        reply = call_gemini(prompt)
        mode = "real"
    else:
        reply = stub_ai(prompt)
        mode = "stub"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env": APP_ENV,
        "version": BUILD_VERSION,
        "mode": mode,
        "prompt": prompt,
        "reply": reply
    }

    write_log(entry)

    return jsonify(entry)

@app.route("/api/logs")
def api_logs():
    return jsonify(read_logs())

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "env": APP_ENV,
        "version": BUILD_VERSION,
        "ai_enabled": USE_REAL_AI
    })

if __name__ == "__main__":
    app.run(debug=True)