#!/usr/bin/env python3
# Render launcher: keeps a tiny HTTP endpoint alive while the Telegram bot polls.
import os
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOT_FILE = os.path.join(os.path.dirname(__file__), 'bilbilak.py')

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Bilbilak is running.\n')
    def log_message(self, format, *args):
        return

port = int(os.getenv('PORT', '10000'))

# Render must provide the Telegram token through an environment variable.
# Do not fall back to input(): Web Services have no interactive terminal.
if not os.getenv('BOT_TOKEN', '').strip():
    print('ERROR: BOT_TOKEN environment variable is not set in Render.', flush=True)
    sys.exit(1)

server = ThreadingHTTPServer(('0.0.0.0', port), HealthHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()

child = None
stopping = False

def stop(*_):
    global stopping
    stopping = True
    if child and child.poll() is None:
        child.terminate()
    server.shutdown()

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

while not stopping:
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    child = subprocess.Popen([sys.executable, '-u', BOT_FILE], cwd=os.path.dirname(BOT_FILE), env=env)
    code = child.wait()
    if stopping:
        break
    # Give Telegram/network a moment before retrying after an unexpected exit.
    import time
    time.sleep(5)

sys.exit(0)
