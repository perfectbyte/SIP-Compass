#!/usr/bin/env sh
# Opens SIP Compass at http://localhost:8765 so the Ask AI tab can reach Ollama. Needs Python 3.8+.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo "Python 3 not found. You can still open SIP-Compass.html directly; only Ask AI needs this."; exit 1; }
exec "$PY" launcher/serve.py
