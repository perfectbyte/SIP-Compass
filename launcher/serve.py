"""SIP Compass local launcher for macOS / Linux. Python 3.8+, standard library only.
Serves the app folder at http://localhost:8765 for this computer only, read-only, app files only."""
import http.server, pathlib, sys, threading, urllib.parse, urllib.request, webbrowser
PORT = 8765
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = f'http://localhost:{PORT}/SIP-Compass.html'
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
         '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.md': 'text/plain; charset=utf-8'}

class Handler(http.server.BaseHTTPRequestHandler):
    def _file(self):
        if self.headers.get('Host') not in (f'localhost:{PORT}', f'127.0.0.1:{PORT}'):
            return None
        rel = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path).lstrip('/') or 'SIP-Compass.html'
        if any(p.startswith(('_', '.')) for p in pathlib.PurePosixPath(rel).parts):
            return None
        f = (ROOT / rel).resolve()
        if ROOT not in f.parents or f.suffix.lower() not in TYPES or not f.is_file():
            return None
        return f
    def _send(self, body):
        f = self._file()
        if not f:
            self.send_error(404); return
        data = f.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', TYPES[f.suffix.lower()])
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if body: self.wfile.write(data)
    def do_GET(self): self._send(True)
    def do_HEAD(self): self._send(False)
    def log_message(self, *a): pass

def main():
    try:
        urllib.request.urlopen(URL, timeout=2); webbrowser.open(URL); return
    except Exception:
        pass
    try:
        srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    except OSError:
        sys.exit(f'Port {PORT} is busy. You can still open SIP-Compass.html directly; only Ask AI needs this launcher.')
    print(f'SIP Compass is open at {URL}\nKeep this window open while you use it. Press Ctrl+C to stop.')
    threading.Timer(0.5, lambda: webbrowser.open(URL)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

if __name__ == '__main__':
    main()
