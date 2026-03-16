import os
import json
from datetime import datetime, timezone
import subprocess
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(override=True)

print(f"DEBUG: APP_ENV is {os.getenv('APP_ENV')}")

app = Flask(__name__)

LOG_FILE = "prompt_logs.jsonl"

def get_app_env():
    return os.getenv("APP_ENV", "dev")
def use_real_ai():
    return os.getenv("USE_REAL_AI", "false").lower() == "true"

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

def get_secret(secret_name: str, region_name: Optional[str] = None) -> dict:
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-2"
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret '{secret_name}': {e}")

    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError(f"Secret '{secret_name}' has no SecretString value.")

    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        return {"value": secret_string}


def get_gemini_api_key() -> Optional[str]:
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key

    secret_name = os.getenv("GEMINI_SECRET_NAME")
    if not secret_name:
        return None

    secret = get_secret(secret_name)

    return (
        secret.get("Gemini_API_Key")
        or secret.get("GEMINI_API_KEY")
        or secret.get("api_key")
        or secret.get("value")
    )


# ---------------- AI ----------------

def stub_ai(prompt: str) -> str:
    return f"(stub mode)\n\nPrompt received:\n{prompt}"

def call_gemini(prompt: str) -> str:
    try:
        api_key = get_gemini_api_key()
        model_name = os.getenv("GEMINI_MODEL", "models/gemini-pro")

        if not api_key:
            return "ERROR: GEMINI_API_KEY not available"

        genai.configure(api_key=api_key)
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
        env=get_app_env(),
        version=BUILD_VERSION
    )

@app.route("/prompts")
def prompts():
    logs = list(reversed(read_logs()))
    return render_template(
        "prompts.html",
        logs=logs,
        env=get_app_env(),
        version=BUILD_VERSION
    )

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if use_real_ai():
        reply = call_gemini(prompt)
        mode = "real"
    else:
        reply = stub_ai(prompt)
        mode = "stub"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env": get_app_env(),
        "version": BUILD_VERSION,
        "mode": mode,
        "prompt": prompt,
        "reply": reply
    }

    write_log(entry)

    return jsonify(entry)

@app.route("/api/logs")
def api_logs():
    return jsonify({"logs": read_logs()})

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "env": get_app_env(),
        "version": BUILD_VERSION,
        "ai_enabled": use_real_ai()
    })

if __name__ == "__main__":
    app.run(debug=True)