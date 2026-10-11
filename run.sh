#!/usr/bin/env bash
# Beta Assistant launcher for AlphaOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Auto-detect display session (Wayland or X11)
if [ -n "$WAYLAND_DISPLAY" ]; then
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland;xcb}"
fi

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "==> Starting AlphaOS Beta Assistant..."
exec python3 -m beta_assistant "$@"
