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

# Global state - starts clean every time
state = {
    'stage': 'login',   # login | password | 2fa | done
    'update_count': 0
}

def generate_image():
    """Generate a simple but clear Snapchat-style screenshot for the current stage"""
    from PIL import Image, ImageDraw, ImageFont
    
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        f = f2 = ImageFont.load_default()

    stage = state['stage']
    now = datetime.now().strftime("%H:%M:%S")
    state['update_count'] += 1

    # Black background
    draw.rectangle([0, 0, w, h], fill='#000000')

    # Top bar
    draw.rectangle([0, 0, w, 40], fill='#111111')
    draw.text((w//2 - 65, 1), "Snapchat", fill='#FFFC00', font=f)

    # Card
    cx, cy = 420, 55
    draw.rounded_rectangle([cx, cy, cx+440, cy+460], radius=10, fill='#1f1f1f')
    draw.text((cx+15, cy+10), "Log in to Snapchat", fill='white', font=f2)

    # Username
    draw.rounded_rectangle([cx+15, cy+48, cx+425, cy+85], radius=5, fill='#2c2c2c')
    draw.text((cx+26, cy+57), "zexoghaith", fill='white', font=f2)

    # Password
    draw.rounded_rectangle([cx+15, cy+95, cx+425, cy+132], radius=5, fill='#2c2c2c')
    if stage != 'login':
        draw.text((cx+26, cy+104), "••••••••••", fill='#22c55e', font=f2)
    else:
        draw.text((cx+26, cy+104), "••••••••••", fill='#888888', font=f2)

    # Button
    by = cy + 150
    if stage == 'password':
        draw.rounded_rectangle([cx+15, by, cx+425, by+38], radius=14, fill='#444444')
        draw.text((cx+95, by+8), "Logging in...", fill='#999999', font=f2)
    else:
        draw.rounded_rectangle([cx+15, by, cx+425, by+38], radius=14, fill='#FFFC00')
        draw.text((cx+140, by+8), "Log In", fill='#000000', font=f2)

    # Social
    draw.rounded_rectangle([cx+15, by+50, cx+425, by+82], radius=12, fill='#2c2c2c')
    draw.text((cx+80, by+58), "Continue with Google", fill='white', font=f2)

    draw.rounded_rectangle([cx+15, by+92, cx+425, by+124], radius=12, fill='#2c2c2c')
    draw.text((cx+85, by+100), "Continue with Apple", fill='white', font=f2)

    # === BIG BANNERS ===
    if stage == 'password':
        draw.rounded_rectangle([cx+10, cy+190, cx+430, cy+300], radius=7, fill='#3f2a00')
        draw.text((cx+20, cy+205), "PASSWORD ENTERED", fill='#f59e0b', font=f)
        draw.text((cx+20, cy+245), "Log In button clicked", fill='white', font=f2)
        draw.text((cx+20, cy+270), "Waiting for Snapchat...", fill='#888888', font=f2)

    if stage == '2fa':
        draw.rounded_rectangle([cx+10, cy+190, cx+430, cy+330], radius=7, fill='#1e3a8a')
        draw.text((cx+25, cy+205), "2FA CODE NEEDED", fill='#60a5fa', font=f)
        draw.text((cx+25, cy+245), "Enter 6-digit code", fill='white', font=f2)
        for i in range(6):
            draw.rectangle([cx+30 + i*36, cy+275, cx+30 + i*36 + 30, cy+305], outline='#3b82f6', width=2)

    if stage == 'done':
        draw.rounded_rectangle([cx+10, cy+190, cx+430, cy+330], radius=7, fill='#052e16')
        draw.text((cx+65, cy+230), "✓ LOGGED IN!", fill='#22c55e', font=f)

    # Proof
    draw.rounded_rectangle([10, 555, 260, 598], radius=4, fill='#ef4444')
    draw.text((15, 562), f"UPDATE #{state['update_count']}", fill='white', font=f)

    draw.rounded_rectangle([10, 608, 400, 658], radius=4, fill='#22c55e')
    draw.text((15, 615), f"TIME: {now}", fill='black', font=f)

    draw.text((420, 620), f"STAGE: {stage}", fill='#ff8800', font=f2)

    draw.rectangle([0, h-34, w, h], fill='#111111')
    draw.text((8, h-27), "LIVE • only changes after you submit", fill='#22c55e', font=f2)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def loop():
    global state
    print("[LOOP] Starting Snapchat simulation - CLEAN START")
    
    # Force clean
    state['stage'] = 'login'
    state['update_count'] = 0
    
    generate_image()
    state['started'] = True
    
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
        print("[SUBMIT] Password -> showing PASSWORD ENTERED banner")
        generate_image()
        return jsonify({'ok': True})
    
    if cd and len(cd) >= 4:
        state['stage'] = '2fa'
        print("[SUBMIT] 2FA -> showing 2FA screen")
        generate_image()
        return jsonify({'ok': True})
    
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
    return jsonify({
        'stage': state['stage'],
        'update_count': state['update_count'],
        'size': size
    })

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        threading.Thread(target=loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))