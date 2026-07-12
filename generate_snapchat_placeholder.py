#!/usr/bin/env python3
"""Generate a highly realistic Snapchat login page screenshot"""
from PIL import Image, ImageDraw, ImageFont
import os

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

def create_realistic_snapchat_login():
    width, height = 1280, 720
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)
    
    # Colors
    SNAP_YELLOW = '#FFFC00'
    WHITE = '#FFFFFF'
    GRAY = '#888888'
    DARK_BG = '#111111'
    CARD_BG = '#1F1F1F'
    FIELD_BG = '#2A2A2A'
    
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_field = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_btn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except:
        font_title = ImageFont.load_default()
        font_header = font_title
        font_field = font_title
        font_btn = font_title
        font_small = font_title
    
    # Top navigation bar (very Snapchat-like)
    draw.rectangle([0, 0, width, 58], fill=DARK_BG)
    
    # Snapchat logo (text style)
    draw.text((width//2 - 95, 8), "Snapchat", fill=SNAP_YELLOW, font=font_title)
    
    # Main centered login card
    card_w, card_h = 420, 510
    cx = (width - card_w) // 2
    cy = 85
    
    # Card shadow effect
    draw.rounded_rectangle([cx+4, cy+4, cx+card_w+4, cy+card_h+4], radius=22, fill='#0A0A0A')
    draw.rounded_rectangle([cx, cy, cx+card_w, cy+card_h], radius=22, fill=CARD_BG)
    
    # Title
    draw.text((cx + 28, cy + 22), "Log in to Snapchat", fill=WHITE, font=font_header)
    
    # Username field
    draw.rounded_rectangle([cx+28, cy+68, cx+card_w-28, cy+110], radius=12, fill=FIELD_BG)
    draw.text((cx + 42, cy + 78), "Username or email", fill=GRAY, font=font_field)
    
    # Password field
    draw.rounded_rectangle([cx+28, cy+125, cx+card_w-28, cy+167], radius=12, fill=FIELD_BG)
    draw.text((cx + 42, cy + 135), "••••••••••", fill=GRAY, font=font_field)
    
    # Log In button (big yellow)
    btn_y = cy + 195
    draw.rounded_rectangle([cx+28, btn_y, cx+card_w-28, btn_y+52], radius=28, fill=SNAP_YELLOW)
    draw.text((cx + 155, btn_y + 14), "Log In", fill='#000000', font=font_btn)
    
    # Divider
    draw.text((cx + 185, btn_y + 65), "or", fill='#555555', font=font_small)
    
    # Continue with Google
    draw.rounded_rectangle([cx+28, btn_y+95, cx+card_w-28, btn_y+140], radius=28, fill=FIELD_BG)
    draw.text((cx + 95, btn_y + 107), "Continue with Google", fill=WHITE, font=font_small)
    
    # Continue with Apple
    draw.rounded_rectangle([cx+28, btn_y+155, cx+card_w-28, btn_y+200], radius=28, fill=FIELD_BG)
    draw.text((cx + 100, btn_y + 167), "Continue with Apple", fill=WHITE, font=font_small)
    
    # Forgot password
    draw.text((cx + 105, cy + 430), "Forgot your password?", fill='#666666', font=font_small)
    
    # Bottom footer
    draw.text((width//2 - 95, height - 38), "accounts.snapchat.com", fill='#444444', font=font_small)
    
    # LIVE indicator (top right)
    draw.rounded_rectangle([width-165, 14, width-18, 44], radius=14, fill='#22c55e')
    draw.text((width-148, 18), "●  LIVE", fill='#000000', font=font_small)
    
    # Subtle "Session active" text
    draw.text((20, height - 35), "Session started — Snapchat login page", fill='#22c55e', font=font_small)
    
    path = os.path.join(STATIC_DIR, 'screenshot.png')
    img.save(path, 'PNG')
    print(f"✅ Created highly realistic Snapchat login screenshot: {path}")
    return path

if __name__ == "__main__":
    create_realistic_snapchat_login()