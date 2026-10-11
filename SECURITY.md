# Privacy and security

SIP Compass is built so that nothing you type leaves your computer.

- **No accounts, no analytics, no tracking.** The app has no backend.
- **Saved data:** goals, holdings and plans are kept in your browser's local storage on your machine. The optional backup file goes wherever you save it.
- **Network requests:** public fund data only (mfapi.in, AMFI), Google Fonts, and, if you use Ask AI, your own Ollama at `127.0.0.1`.
- **The launcher** (`Open SIP Compass.cmd`, `open-sip-compass.sh`) listens only on `localhost:8765`. It serves app files read-only and refuses private folders, the data cache and other hosts.
- **The updater** reads no personal data. It downloads public disclosures and writes `data.js`, `sip-cache.sqlite3` and `update-report.json` into the app folder.

## Reporting a problem

If you find a way that personal data could leave the browser, or a security flaw in the launcher or updater, please open an issue at https://github.com/perfectbyte/SIP-Compass/issues titled **"Security:"** without exploit details. Ask for a private contact in that issue, and the maintainer will reply with one.
