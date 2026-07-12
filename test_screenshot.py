#!/usr/bin/env python3
"""Quick test to verify Snapchat screenshot works"""
import os
import time
from datetime import datetime

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

try:
    from playwright.sync_api import sync_playwright
    
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        print("Navigating to Snapchat login...")
        page.goto('https://accounts.snapchat.com/accounts/login', wait_until='domcontentloaded', timeout=90000)
        print("✅ Successfully loaded Snapchat login page")
        
        time.sleep(3)  # let it render
        
        for i in range(3):
            path = os.path.join(STATIC_DIR, 'screenshot.png')
            page.screenshot(path=path, full_page=False, type='png')
            print(f"✅ Screenshot #{i+1} saved to {path} ({os.path.getsize(path)} bytes)")
            time.sleep(1.5)
        
        print("Test successful! Snapchat login page screenshots are working.")
        browser.close()
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a fallback image
    try:
        from PIL import Image
        img = Image.new('RGB', (1280, 720), color=(200, 50, 50))
        img.save(os.path.join(STATIC_DIR, 'screenshot.png'))
        print("Created error fallback image")
    except:
        pass
