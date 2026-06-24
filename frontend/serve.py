#!/usr/bin/env python3
"""
Tiny static file server for the SafeConnect AI frontend.
Run from the frontend/ directory:

    python3 serve.py
    # or: python3 serve.py 5500

Then open http://localhost:5500/index.html in your browser.
This avoids "file://" CORS issues that can occur when opening HTML files
directly, since the backend API calls use fetch() which behaves more
reliably when the frontend is also served over http://.
"""
import http.server
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5500


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving SafeConnect AI frontend at http://localhost:{PORT}/index.html")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
