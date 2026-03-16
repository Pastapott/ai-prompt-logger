Here is the complete install_dependencies.sh script with the necessary cleanup commands and permission fixes added. This will handle the "Address already in use" and "Permission denied" errors that caused your CodePipeline to fail.

Bash
#!/bin/bash
set -euxo pipefail

DEPLOY_ROOT="/opt/ai-prompt-logger"
APP_DIR="$DEPLOY_ROOT/ai-prompt-logger"
VENV_DIR="$DEPLOY_ROOT/venv"

echo "=== Starting BeforeInstall ==="

echo "Cleaning up old processes and ports..."
dnf install -y psmisc 
sudo fuser -k 8000/tcp || true
sudo pkill -9 -f gunicorn || true

echo "Installing system packages..."
dnf install -y python3 python3-pip git

echo "Ensuring directories exist..."
mkdir -p "$DEPLOY_ROOT"

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

echo "Upgrading pip and installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
"$VENV_DIR/bin/pip" install gunicorn

echo "Ensuring .env and logs exist with correct permissions..."
touch "$APP_DIR/.env"
touch "$APP_DIR/prompt_logs.jsonl"
chmod 666 "$APP_DIR/prompt_logs.jsonl"

echo "Setting ownership to ec2-user..."
chown -R ec2-user:ec2-user "$DEPLOY_ROOT"
chmod -R 755 "$DEPLOY_ROOT"

echo "Creating systemd service..."
cat > /etc/systemd/system/ai-prompt-logger.service <<EOF
[Unit]
Description=AI Prompt Logger Flask App
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=$APP_DIR
# Systemd Environment variables (Step B)
Environment="APP_ENV=prod"
Environment="USE_REAL_AI=true"
Environment="GEMINI_SECRET_NAME=Gemini_API_Key"
Environment="GEMINI_MODEL=gemini-2.0-flash"
ExecStart=$VENV_DIR/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd and restarting service..."
systemctl daemon-reload
systemctl enable ai-prompt-logger
systemctl restart ai-prompt-logger

echo "=== BeforeInstall completed ==="