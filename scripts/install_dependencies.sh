#!/bin/bash
set -e

APP_DIR="/opt/ai-prompt-logger"
VENV_DIR="$APP_DIR/venv"

echo "Installing system packages..."
dnf install -y python3 python3-pip git

echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r "$APP_DIR/requirements.txt"
pip install gunicorn

echo "Setting ownership..."
chown -R ec2-user:ec2-user "$APP_DIR"

echo "Creating systemd service..."
cat > /etc/systemd/system/ai-prompt-logger.service <<EOF
[Unit]
Description=AI Prompt Logger Flask App
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=$APP_DIR
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