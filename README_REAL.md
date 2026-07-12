# REAL Snapchat Login (Playwright)

This version **actually visits** https://accounts.snapchat.com/accounts/login using a real browser (Playwright).

## How it works

1. When you click "Log In" with the phone number:
   - It opens a **real Chromium browser**
   - Navigates to the real Snapchat login page
   - Fills in +47 40300869
   - Clicks the real Log In button

2. Snapchat will send a **real SMS** to +47 40300869

3. When you enter the 6-digit code and submit:
   - The code is typed into the **real page**
   - The real "Verify" / login flow happens

## ⚠️ Important

- **On Railway (this URL)**: Real browser is very hard to run (missing system libraries). It falls back to good-looking generated images.
- **For real behavior**: Run it **locally** on your computer.

## Run locally (REAL mode)

```bash
git clone https://github.com/ghaith012x-collab/snxp.git
cd snxp

pip install -r requirements.txt
playwright install chromium

python app.py
```

Then open http://localhost:5000

Now when you submit the phone, it will **actually** go to Snapchat and trigger a real SMS.

## Current deployed behavior

- Uses real Playwright if available
- Falls back to very realistic generated screenshots
- The flow (phone → "Log In clicked" → SMS boxes) is still correct
