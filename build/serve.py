# Local dev server for the dashboard, with caching disabled so edits show on a normal refresh.
# Usage:  python build/serve.py            (serves repo root on http://localhost:8787/)
#         python build/serve.py 9000        (custom port)
import http.server, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787

class NoCache(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

if __name__ == "__main__":
    print(f"Serving {ROOT} at http://localhost:{PORT}/  (no-cache)")
    http.server.HTTPServer(("127.0.0.1", PORT), NoCache).serve_forever()
