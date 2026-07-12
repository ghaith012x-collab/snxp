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

# Full control state
state = {
    'username': '',
    'password': '',
    'focused': None,          # 'username' | 'password'
    'last_action': 'Click a field on the image, then type in the box below',
    'frame': 0,
}

def get_font(size=14, bold=False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except:
        return ImageFont.load_default()

def generate_image():
    """Realistic clean Snapchat login page - you control everything"""
    state['frame'] += 1
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    f_title = get_font(22, bold=True)
    f_header = get_font(14, bold=True)
    f_field = get_font(15)
    f_small = get_font(11)

    # Browser frame
    draw.rectangle([0, 0, w, 26], fill='#2c2c2c')
    draw.text((10, 6), "●  ●  ●", fill='#666666')
    draw.text((w//2 - 95, 6), "accounts.snapchat.com/accounts/login", fill='#cccccc', font=f_small)

    # Address bar
    draw.rectangle([40, 30, w-40, 52], fill='#1a1a1a', outline='#333333')
    draw.text((50, 34), "https://accounts.snapchat.com/accounts/login", fill='#999999', font=f_small)

    # Page
    draw.rectangle([0, 58, w, h], fill='#000000')

    # Snapchat header
    draw.rectangle([0, 58, w, 96], fill='#111111')
    draw.text((w//2 - 60, 66), "Snapchat", fill='#FFFC00', font=f_title)

    # Login card
    card_w, card_h = 420, 420
    cx = (w - card_w) // 2
    cy = 115

    draw.rounded_rectangle([cx, cy, cx+card_w, cy+card_h], radius=14, fill='#1f1f1f')
    draw.text((cx+18, cy+14), "Log in to Snapchat", fill='white', font=f_header)

    y = cy + 55

    # Username field
    draw.text((cx+18, y), "Username or email or phone", fill='#888888', font=f_small)
    y += 18
    is_u = state['focused'] == 'username'
    draw.rounded_rectangle([cx+16, y, cx+card_w-16, y+36], radius=6, fill='#2a2a2a', outline='#3b82f6' if is_u else '#444444', width=2 if is_u else 1)
    u_text = state['username'] or ''
    draw.text((cx+26, y+9), u_text or "Enter username or phone", fill='#ffffff' if u_text or is_u else '#666666', font=f_field)
    if is_u:
        cur_x = cx + 26 + len(u_text) * 8.4
        draw.rectangle([cur_x, y+7, cur_x+2, y+29], fill='#3b82f6')
    y += 52

    # Password field
    draw.text((cx+18, y), "Password", fill='#888888', font=f_small)
    y += 18
    is_p = state['focused'] == 'password'
    draw.rounded_rectangle([cx+16, y, cx+card_w-16, y+36], radius=6, fill='#2a2a2a', outline='#3b82f6' if is_p else '#444444', width=2 if is_p else 1)
    p_text = '•' * len(state['password']) if state['password'] else ''
    draw.text((cx+26, y+9), p_text or "Enter password", fill='#ffffff' if p_text or is_p else '#666666', font=f_field)
    if is_p:
        cur_x = cx + 26 + len(p_text) * 8.4
        draw.rectangle([cur_x, y+7, cur_x+2, y+29], fill='#3b82f6')
    y += 55

    # Yellow Log In button
    draw.rounded_rectangle([cx+16, y, cx+card_w-16, y+42], radius=22, fill='#FFFC00')
    draw.text((cx+155, y+10), "Log In", fill='#000000', font=f_header)

    y += 58
    draw.text((cx+185, y), "or", fill='#555555', font=f_small)
    y += 22

    draw.rounded_rectangle([cx+16, y, cx+card_w-16, y+32], radius=20, fill='#2c2c2c')
    draw.text((cx+100, y+7), "Continue with Google", fill='#dddddd', font=f_small)
    y += 40

    draw.rounded_rectangle([cx+16, y, cx+card_w-16, y+32], radius=20, fill='#2c2c2c')
    draw.text((cx+105, y+7), "Continue with Apple", fill='#dddddd', font=f_small)

    # Forgot
    draw.text((cx+95, cy + card_h - 30), "Forgot your password?", fill='#555555', font=f_small)

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

# ================== API ==================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/click', methods=['POST'])
def do_click():
    data = request.get_json() or {}
    x = int(data.get('x', 0))
    y = int(data.get('y', 0))

    # Tuned click zones for the current image layout
    if 170 < y < 210:           # username field
        state['focused'] = 'username'
        state['last_action'] = 'Focused username field'
    elif 265 < y < 305:         # password field
        state['focused'] = 'password'
        state['last_action'] = 'Focused password field'
    elif 320 < y < 365:         # Log In button
        state['last_action'] = 'Clicked Log In'
        state['focused'] = None
    else:
        state['last_action'] = f'Clicked ({x},{y})'

    generate_image()
    return jsonify({'ok': True, 'focused': state['focused'], 'action': state['last_action']})

@app.route('/type', methods=['POST'])
def do_type():
    data = request.get_json() or {}
    text = data.get('text', '')

    if not state['focused']:
        state['focused'] = 'username'

    if state['focused'] == 'username':
        state['username'] += text
        state['last_action'] = 'Typing in username...'
    elif state['focused'] == 'password':
        state['password'] += text
        state['last_action'] = 'Typing in password...'

    generate_image()
    return jsonify({'ok': True})

@app.route('/key', methods=['POST'])
def do_key():
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
    return jsonify({'ok': True, 'action': state['last_action']})

@app.route('/reset', methods=['POST'])
def do_reset():
    state.update({
        'username': '',
        'password': '',
        'focused': None,
        'last_action': 'Clean login page'
    })
    generate_image()
    return jsonify({'ok': True})

@app.route('/screenshot')
def get_shot():
    generate_image()
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def get_status():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({**state, 'size': size})

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        generate_image()
        threading.Thread(target=screenshot_loop, daemon=True).start()
        print("[LIVE CAM] Clean full control Snapchat ready")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))