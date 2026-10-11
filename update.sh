#!/usr/bin/env sh
# SIP Compass - refresh public fund data on macOS / Linux. Needs Python 3.10+.
# Usage: sh update.sh
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo "Python 3.10+ not found. Install it from https://www.python.org/downloads/"; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || { echo "Python 3.10 or later is needed."; exit 1; }
"$PY" updater/update_data.py --output "$(pwd)"
rc=$?
[ $rc -eq 0 ] && echo "Update complete. Reload SIP-Compass.html in your browser."
[ $rc -eq 2 ] && echo "Finished with some sources unavailable; usable data kept. See update-report.json."
exit $rc
