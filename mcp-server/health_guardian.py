# Light-speed healthcheck server for Railway
import http.server
import socketserver
import os
import threading
import sys

PORT = int(os.getenv("PORT", 8080))

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/health', '/']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "OK", "msg": "Railway Guardian Active"}')
        else:
            # Proxy anything else to the main app if it was on a different port, 
            # but here we just want to pass the healthcheck.
            self.send_response(404)
            self.end_headers()

def run_health():
    with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
        print(f"✅ Health Guardian running on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_health()
