#!/bin/bash
set -e

echo "Stopping existing app service if running..."

if systemctl list-units --full -all | grep -Fq "ai-prompt-logger.service"; then
    systemctl stop ai-prompt-logger || true
fi