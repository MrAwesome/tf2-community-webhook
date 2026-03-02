#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT_DIR="${HOME}/.config/systemd/user"

mkdir -p "$UNIT_DIR"
ln -sf "${SCRIPT_DIR}/tf2-server-list.service" "$UNIT_DIR/"
ln -sf "${SCRIPT_DIR}/tf2-server-list.timer" "$UNIT_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now tf2-server-list.timer

echo "Timer installed. Check status with: systemctl --user status tf2-server-list.timer"
