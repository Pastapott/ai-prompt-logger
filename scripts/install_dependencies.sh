#!/bin/bash
set -euxo pipefail

DEPLOY_ROOT="/opt/ai-prompt-logger"
APP_DIR="$DEPLOY_ROOT/ai-prompt-logger"
VENV_DIR="$DEPLOY_ROOT/venv"

echo "=== Starting BeforeInstall ==="
echo "DEPLOY_ROOT=$DEPLOY_ROOT"
echo "APP_DIR=$APP_DIR"
echo "VENV_DIR=$VENV_DIR"

echo "Installing system packages..."
dnf install -y python3 python3-pip git

echo "Ensuring directories exist..."
mkdir -p "$DEPLOY_ROOT"

echo "Listing deploy root..."
ls -la "$DEPLOY_ROOT"
echo "Listing app dir..."
ls -la "$APP_DIR"

echo "Checking requirements file exists..."
test -f "$APP_DIR/requirements.txt"

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

echo "Upgrading pip..."
"$VENV_DIR/bin/pip" install --upgrade pip

echo "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
"$VENV_DIR/bin/pip" install gunicorn

echo "Ensuring .env file exists..."
touch "$APP_DIR/.env"
chown ec2-user:ec2-user "$APP_DIR/.env"
chmod 640 "$APP_DIR/.env"

echo "Setting ownership..."
chown -R ec2-user:ec2-user "$DEPLOY_ROOT"

echo "Creating systemd service..."
cat > /etc/systemd/system/ai-prompt-logger.service <<EOF
[Unit]
Description=AI Prompt Logger Flask App
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment="APP_ENV=prod"
Environment="USE_REAL_AI=false"
ExecStart=$VENV_DIR/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd..."
systemctl daemon-reload
systemctl enable ai-prompt-logger

echo "=== BeforeInstall completed ==="