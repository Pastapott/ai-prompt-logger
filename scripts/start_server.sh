#!/bin/bash
set -e

echo "Starting app service..."
systemctl restart ai-prompt-logger
systemctl status ai-prompt-logger --no-pager