import os
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

state = {
    'username': '',
    'password': '',
    'focused': None,
    'last_action': 'Click a field in the image, then type in the box below',
    'frame': 0,
}

def get_font(size=14, bold=False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except:
        return ImageFont.load_default()

def generate_image():
    state['frame'] += 1
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    f_title = get_font(22, bold=True)
    f_header = get_font(14, bold=True)
    f_field = get_font(15)
    f_small = get_font(11)

    # Browser top
    draw.rectangle([0, 0, w, 26], fill='#2c2c2c')
    draw.text((10, 6), "●  ●  ●", fill='#666')
    draw.text((w//2 - 95, 6), "accounts.snapchat.com/accounts/login", fill='#ccc', font=f_small)

    draw.rectangle([40, 30, w-40, 52], fill='#1a1a1a', outline='#333')
    draw.text((50, 34), "https://accounts.snapchat.com/accounts/login", fill='#999', font=f_small)

    draw.rectangle([0, 58, w, h], fill='#000000')

    # Snapchat header
    draw.rectangle([0, 58, w, 96], fill='#111111')
    draw.text((w//2 - 60, 66), "Snapchat", fill='#FFFC00', font=f_title)

    # Login card - bigger and more realistic
    card_w, card_h = 440, 450
    cx = (w - card_w) // 2
    cy = 108

    draw.rounded_rectangle([cx, cy, cx+card_w, cy+card_h], radius=16, fill='#1f1f1f')
    draw.text((cx+20, cy+16), "Log in to Snapchat", fill='white', font=f_header)

    y = cy + 58

    # Username field - VERY obvious
    draw.text((cx+18, y), "Username, email or phone", fill='#888', font=f_small)
    y += 18
    is_u = state['focused'] == 'username'
    draw.rounded_rectangle([cx+12, y, cx+card_w-12, y+42], radius=8, fill='#222', outline='#3b82f6' if is_u else '#555', width=4 if is_u else 1)
    u = state['username'] or ''
    draw.text((cx+22, y+11), u or "click and type here", fill='#fff' if u or is_u else '#777', font=f_field)
    if is_u:
        cxu = cx + 22 + len(u) * 8.6
        draw.rectangle([cxu, y+9, cxu+2, y+33], fill='#3b82f6')
    y += 58

    # Password field - VERY obvious
    draw.text((cx+18, y), "Password", fill='#888', font=f_small)
    y += 18
    is_p = state['focused'] == 'password'
    draw.rounded_rectangle([cx+12, y, cx+card_w-12, y+42], radius=8, fill='#222', outline='#3b82f6' if is_p else '#555', width=4 if is_p else 1)
    p = '•' * len(state['password']) if state['password'] else ''
    draw.text((cx+22, y+11), p or "click and type here", fill='#fff' if p or is_p else '#777', font=f_field)
    if is_p:
        cxp = cx + 22 + len(p) * 8.6
        draw.rectangle([cxp, y+9, cxp+2, y+33], fill='#3b82f6')
    y += 58

    # Log In button
    draw.rounded_rectangle([cx+12, y, cx+card_w-12, y+44], radius=22, fill='#FFFC00')
    draw.text((cx+155, y+11), "Log In", fill='#000', font=f_header)

    # Social
    y += 60
    draw.text((cx+190, y), "or", fill='#555', font=f_small)
    y += 20
    draw.rounded_rectangle([cx+12, y, cx+card_w-12, y+32], radius=20, fill='#2c2c2c')
    draw.text((cx+100, y+7), "Continue with Google", fill='#ddd', font=f_small)
    y += 38
    draw.rounded_rectangle([cx+12, y, cx+card_w-12, y+32], radius=20, fill='#2c2c2c')
    draw.text((cx+105, y+7), "Continue with Apple", fill='#ddd', font=f_small)

    draw.text((cx+95, cy+card_h-28), "Forgot your password?", fill='#555', font=f_small)

    # Live bar
    draw.rectangle([0, h-24, w, h], fill='#111111')
    draw.text((10, h-18), f"LIVE CAM  •  {state['last_action']}  •  frame {state['frame']}", fill='#22c55e', font=f_small)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def screenshot_loop():
    while True:
        generate_image()
        time.sleep(0.6)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/click', methods=['POST'])
def click():
    data = request.get_json() or {}
    x = int(data.get('x', 0))
    y = int(data.get('y', 0))

    # Very generous and accurate zones
    if 165 < y < 225 and 420 < x < 860:      # username
        state['focused'] = 'username'
        state['last_action'] = 'Focused username field - type in the box below'
    elif 265 < y < 325 and 420 < x < 860:    # password
        state['focused'] = 'password'
        state['last_action'] = 'Focused password field - type in the box below'
    elif 325 < y < 380 and 420 < x < 860:    # Log In
        state['last_action'] = 'Clicked Log In'
        state['focused'] = None
    else:
        state['last_action'] = f'Clicked ({x},{y}) - click the input fields'

    generate_image()
    return jsonify({'ok': True, 'focused': state['focused'], 'action': state['last_action']})

@app.route('/type', methods=['POST'])
def type_text():
    data = request.get_json() or {}
    text = data.get('text', '')

    if not state['focused']:
        state['focused'] = 'username'

    if state['focused'] == 'username':
        state['username'] += text
        state['last_action'] = 'Typing...'
    elif state['focused'] == 'password':
        state['password'] += text
        state['last_action'] = 'Typing password...'

    generate_image()
    return jsonify({'ok': True})

@app.route('/key', methods=['POST'])
def key():
    data = request.get_json() or {}
    key = data.get('key', '')

    if key == 'Backspace':
        if state['focused'] == 'username' and state['username']:
            state['username'] = state['username'][:-1]
        elif state['focused'] == 'password' and state['password']:
            state['password'] = state['password'][:-1]
        state['last_action'] = 'Backspace'
    elif key == 'Enter':
        if state['focused'] == 'password':
            state['last_action'] = 'Pressed Enter'
            state['focused'] = None
        else:
            state['focused'] = 'password'
            state['last_action'] = 'Pressed Enter'

    generate_image()
    return jsonify({'ok': True})

@app.route('/reset', methods=['POST'])
def reset():
    state.update({
        'username': '',
        'password': '',
        'focused': None,
        'last_action': 'Clean login page'
    })
    generate_image()
    return jsonify({'ok': True})

@app.route('/screenshot')
def shot():
    generate_image()
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def stat():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({**state, 'size': size})

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        generate_image()
        threading.Thread(target=screenshot_loop, daemon=True).start()
        print("[LIVE] Full control ready")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))