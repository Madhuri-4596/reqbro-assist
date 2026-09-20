"""Local demo server: static UI plus a narrow proxy to the deployed API."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import os

STATIC_DIR = Path(__file__).parent / "backend" / "app" / "static"
UPSTREAM = "https://reqbro-assist-production.up.railway.app"
ALLOWED = {"/api/debug", "/api/health"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _proxy(self):
        if self.path not in ALLOWED:
            self.send_error(404)
            return
        length = min(int(self.headers.get("Content-Length", "0")), 64_000)
        body = self.rfile.read(length) if length else None
        request = Request(
            UPSTREAM + self.path,
            data=body,
            method=self.command,
            headers={"Content-Type": "application/json"},
        )
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        payload = response.read()
        self.send_response(response.status)
        self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        self._proxy()

    def do_GET(self):
        if self.path in ALLOWED:
            self._proxy()
        else:
            super().do_GET()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3240"))
    print(f"ReqBro preview: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
