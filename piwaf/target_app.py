from flask import Flask, request, render_template_string, redirect, session
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'target-bank-2026'

USERS = {
    'user':  {'password': 'user',  'name': 'user',   'acc': '****4821', 'balance': '₹2,84,320.50'},
    'admin': {'password': 'admin', 'name': 'admin',  'acc': '****0001', 'balance': '₹0.00'},
}

TRANSACTIONS = [
    {'date':'12 Mar 2026','desc':'NEFT - Amazon Pay',         'amount':'-₹4,299', 'type':'debit', 'bal':'₹2,84,320'},
    {'date':'11 Mar 2026','desc':'Salary Credit - Infosys Ltd','amount':'+₹95,000','type':'credit','bal':'₹2,88,619'},
    {'date':'10 Mar 2026','desc':'UPI - Swiggy',              'amount':'-₹450',   'type':'debit', 'bal':'₹1,93,619'},
    {'date':'09 Mar 2026','desc':'IMPS - Rent Payment',       'amount':'-₹18,000','type':'debit', 'bal':'₹1,94,069'},
    {'date':'08 Mar 2026','desc':'ATM Withdrawal',            'amount':'-₹5,000', 'type':'debit', 'bal':'₹2,12,069'},
    {'date':'07 Mar 2026','desc':'FD Interest Credit',        'amount':'+₹3,240', 'type':'credit','bal':'₹2,17,069'},
    {'date':'06 Mar 2026','desc':'Bill Pay - BESCOM',         'amount':'-₹1,840', 'type':'debit', 'bal':'₹2,13,829'},
    {'date':'05 Mar 2026','desc':'UPI - Zomato',              'amount':'-₹320',   'type':'debit', 'bal':'₹2,15,669'},
]

ALL_USERS = [
    {'id':'USR001','name':'user',    'username':'user',    'acc':'SB****4821','balance':'₹2,84,320.50','status':'Active',   'kyc':'Verified','joined':'12 Jan 2024'},
    {'id':'USR002','name':'Priya Sharma','username':'priya.s', 'acc':'SB****2934','balance':'₹1,12,450.00','status':'Active',   'kyc':'Verified','joined':'05 Mar 2024'},
    {'id':'USR003','name':'Rahul Mehta', 'username':'rahul.m', 'acc':'SB****7821','balance':'₹45,200.75', 'status':'Suspended','kyc':'Pending', 'joined':'18 Jun 2024'},
    {'id':'USR004','name':'Anjali Nair', 'username':'anjali.n','acc':'SB****3312','balance':'₹8,92,100.00','status':'Active',   'kyc':'Verified','joined':'22 Aug 2024'},
    {'id':'USR005','name':'Vikram Singh','username':'vikram.s','acc':'SB****9901','balance':'₹3,200.00',  'status':'Locked',   'kyc':'Failed',  'joined':'01 Nov 2024'},
]

ALL_TXNS = [
    {'id':'TXN001','date':'12 Mar 2026','from':'USR001',    'to':'Amazon Pay', 'amount':'₹4,299',  'type':'Debit',   'status':'Success','flag':''},
    {'id':'TXN002','date':'11 Mar 2026','from':'Infosys Ltd','to':'USR001',   'amount':'₹95,000', 'type':'Credit',  'status':'Success','flag':''},
    {'id':'TXN003','date':'10 Mar 2026','from':'USR002',    'to':'USR004',    'amount':'₹50,000', 'type':'Transfer','status':'Success','flag':'Suspicious'},
    {'id':'TXN004','date':'09 Mar 2026','from':'USR001',    'to':'Landlord',  'amount':'₹18,000', 'type':'Debit',   'status':'Success','flag':''},
    {'id':'TXN005','date':'08 Mar 2026','from':'USR003',    'to':'Unknown',   'amount':'₹2,00,000','type':'Transfer','status':'Blocked','flag':'Fraud'},
    {'id':'TXN006','date':'07 Mar 2026','from':'USR004',    'to':'USR005',    'amount':'₹1,500',  'type':'Transfer','status':'Success','flag':''},
    {'id':'TXN007','date':'06 Mar 2026','from':'USR005',    'to':'Foreign Acc','amount':'₹75,000','type':'Transfer','status':'Blocked','flag':'Fraud'},
]

# ── Shared CSS ─────────────────────────────────────────────────────────────────
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh;}
nav{background:#003366;padding:0 40px;height:60px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(0,0,0,.3);}
.logo{display:flex;align-items:center;gap:10px;color:#fff;font-size:20px;font-weight:700;}
.logo svg{width:32px;height:32px;}
.nav-r{display:flex;align-items:center;gap:20px;}
.nl{color:rgba(255,255,255,.8);text-decoration:none;font-size:13px;font-weight:500;}
.nl:hover{color:#fff;}
.nb{background:#e8b800;color:#003366;padding:7px 16px;font-size:13px;font-weight:700;text-decoration:none;border:none;cursor:pointer;}
.nb:hover{background:#ffd000;}
.container{max-width:1100px;margin:0 auto;padding:30px 20px;}
.card{background:#fff;border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.1);padding:24px;margin-bottom:20px;}
.btn{padding:10px 24px;font-size:14px;font-weight:600;border:none;cursor:pointer;font-family:'Inter',sans-serif;text-decoration:none;display:inline-block;}
.btn-p{background:#003366;color:#fff;}
.btn-p:hover{background:#004488;}
.btn-g{background:#e8b800;color:#003366;}
.btn-g:hover{background:#ffd000;}
.inp{width:100%;padding:10px 14px;border:1px solid #ddd;font-size:14px;font-family:'Inter',sans-serif;outline:none;}
.inp:focus{border-color:#003366;}
.err{background:#fff0f0;border:1px solid #ffcccc;color:#c00;padding:10px 14px;margin-bottom:16px;font-size:13px;}
.ok{background:#f0fff4;border:1px solid #b2dfdb;color:#006644;padding:10px 14px;margin-bottom:16px;font-size:13px;}
.lbl{font-size:12px;font-weight:600;color:#555;display:block;margin-bottom:5px;}
footer{background:#003366;color:rgba(255,255,255,.6);text-align:center;padding:16px;font-size:12px;margin-top:40px;}
table{width:100%;border-collapse:collapse;}
th{padding:10px 12px;text-align:left;font-size:12px;color:#555;border-bottom:2px solid #e0e0e0;background:#f8f9fa;}
td{padding:10px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;}
.cr{color:#2e7d32;font-weight:600;}
.dr{color:#c62828;font-weight:600;}
</style>"""

ADMIN_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh;display:flex;flex-direction:column;}
.anav{background:#1a0533;padding:0 30px;height:56px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(0,0,0,.4);}
.anav-logo{display:flex;align-items:center;gap:10px;color:#fff;font-size:17px;font-weight:700;}
.anav-logo span{background:#e8b800;color:#1a0533;padding:2px 8px;font-size:11px;font-weight:800;letter-spacing:1px;}
.anav-r{display:flex;align-items:center;gap:16px;font-size:13px;color:rgba(255,255,255,.7);}
.anav-r a{color:rgba(255,255,255,.7);text-decoration:none;}
.anav-r a:hover{color:#fff;}
.layout{display:flex;flex:1;}
.sidebar{width:210px;background:#fff;border-right:1px solid #e0e0e0;padding:20px 0;flex-shrink:0;}
.sb-sec{font-size:10px;font-weight:700;color:#999;letter-spacing:1.5px;text-transform:uppercase;padding:12px 20px 5px;}
.sb-item{display:flex;align-items:center;gap:10px;padding:10px 20px;font-size:13px;color:#444;text-decoration:none;border-left:3px solid transparent;}
.sb-item:hover{background:#f8f9fa;color:#1a0533;}
.sb-item.active{color:#1a0533;border-left-color:#e8b800;background:#fef9e7;font-weight:600;}
.content{flex:1;padding:24px;}
.page-title{font-size:20px;font-weight:700;color:#1a0533;margin-bottom:20px;}
.acard{background:#fff;border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.08);padding:20px;margin-bottom:20px;}
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px;}
.stat{background:#fff;border-radius:4px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.08);border-top:3px solid #e8b800;}
.stat-val{font-size:28px;font-weight:800;color:#1a0533;}
.stat-lbl{font-size:12px;color:#888;margin-top:4px;}
table{width:100%;border-collapse:collapse;}
th{padding:10px 12px;text-align:left;font-size:11px;color:#888;border-bottom:2px solid #e0e0e0;background:#f8f9fa;text-transform:uppercase;letter-spacing:.5px;}
td{padding:10px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;}
tr:hover td{background:#fafafa;}
.badge{padding:2px 8px;font-size:11px;font-weight:600;border-radius:2px;}
.badge-ok{background:#e8f5e9;color:#2e7d32;}
.badge-warn{background:#fff8e1;color:#f57f17;}
.badge-err{background:#ffebee;color:#c62828;}
.badge-info{background:#e3f2fd;color:#1565c0;}
.inp{padding:8px 12px;border:1px solid #ddd;font-size:13px;font-family:'Inter',sans-serif;outline:none;}
.inp:focus{border-color:#1a0533;}
.btn{padding:7px 16px;font-size:12px;font-weight:600;border:none;cursor:pointer;font-family:'Inter',sans-serif;text-decoration:none;display:inline-block;border-radius:2px;}
.btn-p{background:#1a0533;color:#fff;}
.btn-p:hover{background:#2d0855;}
.btn-r{background:#ffebee;color:#c62828;border:1px solid #ffcdd2;}
.btn-r:hover{background:#ffcdd2;}
.btn-g{background:#e8f5e9;color:#2e7d32;border:1px solid #c8e6c9;}
.btn-y{background:#fff8e1;color:#f57f17;border:1px solid #ffe082;}
</style>"""

# ── Helpers ────────────────────────────────────────────────────────────────────
LOGO_SVG = '''<svg viewBox="0 0 40 40" fill="none"><rect width="40" height="40" rx="4" fill="#e8b800"/><path d="M8 28V16l12-8 12 8v12H8z" fill="#003366"/><rect x="15" y="20" width="10" height="8" fill="#e8b800"/></svg>'''

def nav(user=None):
    if user:
        return f'<nav><div class="logo">{LOGO_SVG}SecureBank</div><div class="nav-r"><span style="color:rgba(255,255,255,.7);font-size:13px">Welcome, {user}</span><a href="/dashboard" class="nl">Dashboard</a><a href="/transfer" class="nl">Transfer</a><a href="/bills" class="nl">Bills</a><a href="/logout" class="nl">Logout</a></div></nav>'
    return f'<nav><div class="logo">{LOGO_SVG}SecureBank</div><div class="nav-r"><a href="/" class="nl">Home</a><a href="/about" class="nl">About</a><a href="/contact" class="nl">Contact</a><a href="/login" class="nb">Login</a></div></nav>'

def footer():
    return '<footer>&copy; 2026 SecureBank Ltd. &nbsp;|&nbsp; DICGC Insured &nbsp;|&nbsp; RBI Regulated &nbsp;|&nbsp; ISO 27001 Certified</footer>'

def admin_nav():
    return '<div class="anav"><div class="anav-logo">SecureBank <span>ADMIN</span></div><div class="anav-r"><span>Logged in as: <strong style="color:#e8b800">Administrator</strong></span><a href="/admin/logs">Audit Logs</a><a href="/logout" style="color:#ff6b6b">Logout</a></div></div>'

def admin_sidebar(active=''):
    items = [('overview','Overview','&#9632;'),('users','User Management','&#128100;'),('transactions','Transactions','&#128196;'),('fraud','Fraud Alerts','&#9888;'),('system','System Settings','&#9881;')]
    html = '<div class="sidebar"><div class="sb-sec">Main Menu</div>'
    for key,label,icon in items:
        cls = 'active' if active==key else ''
        html += f'<a href="/admin/{key}" class="sb-item {cls}">{icon} &nbsp;{label}</a>'
    html += '<div class="sb-sec">Reports</div><a href="/admin/logs" class="sb-item">&#128221; &nbsp;Audit Logs</a></div>'
    return html

# ── User Routes ────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    q = request.args.get('q','')
    sr = f'<div style="margin-top:14px;padding:12px;background:#f8f9fa;border:1px solid #e0e0e0;font-size:13px;">Results for: <strong>{q}</strong><br><span style="color:#999;font-size:12px;">0 results found.</span></div>' if q else ''
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank</title>{CSS}</head><body>
{nav()}
<div style="background:linear-gradient(135deg,#003366 0%,#005599 100%);color:#fff;padding:70px 40px;text-align:center;">
  <h1 style="font-size:38px;font-weight:700;margin-bottom:12px">Banking Made Simple &amp; Secure</h1>
  <p style="font-size:16px;opacity:.85;margin-bottom:28px">Trusted by over 2 million customers across India</p>
  <a href="/login" style="background:#e8b800;color:#003366;padding:12px 32px;font-weight:700;text-decoration:none;font-size:15px;margin-right:12px">Internet Banking</a>
  <a href="/register" style="background:transparent;color:#fff;padding:12px 32px;font-weight:600;text-decoration:none;font-size:15px;border:2px solid rgba(255,255,255,.5)">Open Account</a>
</div>
<div class="container" style="margin-top:30px;">
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:30px;">
    <div class="card" style="text-align:center;border-top:3px solid #003366"><h3 style="margin-bottom:6px;color:#003366">Savings Account</h3><p style="font-size:13px;color:#666">Earn up to 7% interest p.a.</p></div>
    <div class="card" style="text-align:center;border-top:3px solid #e8b800"><h3 style="margin-bottom:6px;color:#003366">Credit Cards</h3><p style="font-size:13px;color:#666">Zero annual fee. Cashback on every purchase</p></div>
    <div class="card" style="text-align:center;border-top:3px solid #003366"><h3 style="margin-bottom:6px;color:#003366">Fixed Deposits</h3><p style="font-size:13px;color:#666">Lock in rates up to 8.5%</p></div>
  </div>
  <div class="card">
    <h3 style="margin-bottom:14px;color:#003366">Search Transactions / Help</h3>
    <form action="/" method="GET" style="display:flex;gap:10px;">
      <input class="inp" name="q" placeholder="Search by keyword, transaction ID, amount..." value="{q}">
      <button class="btn btn-p" type="submit">Search</button>
    </form>{sr}
  </div>
</div>
{footer()}</body></html>'''

@app.route('/login', methods=['GET','POST'])
def login():
    error = ''
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        if u in USERS and USERS[u]['password'] == p:
            session['user'] = USERS[u]['name']
            session['acc'] = u
            return redirect('/admin' if u == 'admin' else '/dashboard')
        error = '<div class="err">Invalid Customer ID or Password. Please try again.</div>'
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Login</title>{CSS}</head><body>
{nav()}
<div class="container" style="max-width:420px;padding-top:50px;">
  <div class="card" style="border-top:4px solid #003366;">
    <div style="text-align:center;margin-bottom:24px;">
      <h2 style="color:#003366;font-size:22px;">Internet Banking Login</h2>
      <p style="font-size:12px;color:#999;margin-top:4px;">Secure 256-bit SSL Encrypted</p>
    </div>
    {error}
    <form method="POST">
      <div style="margin-bottom:14px;"><label class="lbl">Customer ID / Username</label><input class="inp" type="text" name="username" placeholder="Enter Customer ID" required autofocus></div>
      <div style="margin-bottom:20px;"><label class="lbl">Password / IPIN</label><input class="inp" type="password" name="password" placeholder="Enter Password"></div>
      <button class="btn btn-p" style="width:100%" type="submit">Login to NetBanking</button>
    </form>
    <div style="margin-top:16px;display:flex;justify-content:space-between;">
      <a href="/forgot" style="font-size:12px;color:#003366;text-decoration:none;">Forgot Password?</a>
      <a href="/register" style="font-size:12px;color:#003366;text-decoration:none;">New User? Register</a>
    </div>
    <div style="margin-top:20px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#999;text-align:center;">
      For security, always verify you are on<br><strong>https://securebank.in</strong> before logging in
    </div>
  </div>
</div>
{footer()}</body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if not session.get('user'): return redirect('/login')
    u = USERS[session['acc']]
    filt = request.args.get('filter','')
    txns = [t for t in TRANSACTIONS if filt.lower() in t['desc'].lower()] if filt else TRANSACTIONS
    rows = ''.join([f'<tr><td style="color:#666">{t["date"]}</td><td>{t["desc"]}</td><td class="{"cr" if t["type"]=="credit" else "dr"}" style="text-align:right">{t["amount"]}</td><td style="text-align:right;color:#999;font-size:12px">{t["bal"]}</td></tr>' for t in txns])
    acc_result = f'<div style="margin-top:12px;padding:10px;background:#f8f9fa;border:1px solid #e0e0e0;font-size:13px;">Looking up: <strong>{request.args.get("id")}</strong><br><span style="color:#999;font-size:12px;">No records found.</span></div>' if request.args.get('id') else ''
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Dashboard</title>{CSS}</head><body>
{nav(session["user"])}
<div style="background:#003366;padding:16px 40px;display:flex;justify-content:space-between;align-items:center;">
  <div><div style="color:rgba(255,255,255,.7);font-size:12px;">Account Summary</div><div style="color:#fff;font-size:18px;font-weight:700;">{u["name"]}</div></div>
  <div style="text-align:right;"><div style="color:rgba(255,255,255,.7);font-size:12px;">Last Login: Today 08:32 AM</div><div style="color:#e8b800;font-size:12px;margin-top:2px;">Secure Session Active</div></div>
</div>
<div class="container">
  <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:16px;margin-bottom:20px;">
    <div class="card" style="border-left:4px solid #003366"><div style="font-size:12px;color:#999;margin-bottom:4px;">Savings Account {u["acc"]}</div><div style="font-size:32px;font-weight:700;color:#003366">{u["balance"]}</div><div style="font-size:12px;color:#2e7d32;margin-top:4px;">Available Balance</div></div>
    <div class="card" style="text-align:center;border-left:4px solid #e8b800"><div style="font-size:12px;color:#999;margin-bottom:8px">Quick Transfer</div><a href="/transfer" class="btn btn-p" style="font-size:13px;padding:8px 18px">Transfer Now</a></div>
    <div class="card" style="text-align:center;border-left:4px solid #2e7d32"><div style="font-size:12px;color:#999;margin-bottom:8px">Pay Bills</div><a href="/bills" class="btn btn-p" style="font-size:13px;padding:8px 18px;background:#2e7d32">Pay Now</a></div>
  </div>
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3 style="color:#003366">Recent Transactions</h3>
      <form action="/dashboard" method="GET" style="display:flex;gap:8px;">
        <input class="inp" name="filter" style="width:200px" placeholder="Filter transactions..." value="{filt}">
        <button class="btn btn-p" style="padding:8px 16px;font-size:13px">Filter</button>
      </form>
    </div>
    <table><thead><tr><th>Date</th><th>Description</th><th style="text-align:right">Amount</th><th style="text-align:right">Balance</th></tr></thead><tbody>{rows}</tbody></table>
  </div>
  <div class="card">
    <h3 style="color:#003366;margin-bottom:14px">Account Lookup</h3>
    <form action="/dashboard" method="GET" style="display:flex;gap:10px;">
      <input class="inp" name="id" placeholder="Enter Account ID or User ID..." value="{request.args.get('id','')}">
      <button class="btn btn-g" type="submit">Lookup</button>
    </form>{acc_result}
  </div>
</div>
{footer()}</body></html>'''

@app.route('/transfer', methods=['GET','POST'])
def transfer():
    if not session.get('user'): return redirect('/login')
    msg = ''
    if request.method == 'POST':
        msg = f'<div class="ok">Transfer of ₹{request.form.get("amount","0")} to {request.form.get("to_name","N/A")} initiated. Ref: TXN{random.randint(100000,999999)}</div>'
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Transfer</title>{CSS}</head><body>
{nav(session["user"])}
<div class="container" style="max-width:560px;padding-top:30px;">
  <div class="card" style="border-top:4px solid #e8b800">
    <h2 style="color:#003366;margin-bottom:20px">Fund Transfer</h2>{msg}
    <form method="POST">
      <div style="margin-bottom:14px"><label class="lbl">Beneficiary Account Number</label><input class="inp" type="text" name="to_acc" placeholder="Enter account number" required></div>
      <div style="margin-bottom:14px"><label class="lbl">Beneficiary Name</label><input class="inp" type="text" name="to_name" placeholder="Enter beneficiary name"></div>
      <div style="margin-bottom:14px"><label class="lbl">Amount (₹)</label><input class="inp" type="number" name="amount" placeholder="0.00" min="1"></div>
      <div style="margin-bottom:14px"><label class="lbl">Remarks</label><input class="inp" type="text" name="remarks" placeholder="Optional remarks"></div>
      <div style="margin-bottom:20px"><label class="lbl">Transfer Mode</label><select class="inp" name="mode"><option>NEFT</option><option>IMPS</option><option>RTGS</option><option>UPI</option></select></div>
      <button class="btn btn-p" style="width:100%" type="submit">Confirm Transfer</button>
    </form>
  </div>
</div>
{footer()}</body></html>'''

@app.route('/contact', methods=['GET','POST'])
def contact():
    msg = '<div class="ok">Your request has been submitted. We will respond within 24 hours.</div>' if request.method == 'POST' else ''
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Contact</title>{CSS}</head><body>
{nav(session.get("user"))}
<div class="container" style="max-width:600px;padding-top:30px;">
  <div class="card">
    <h2 style="color:#003366;margin-bottom:6px">Contact Support</h2>
    <p style="font-size:13px;color:#666;margin-bottom:20px">24/7 Customer Support — 1800-XXX-XXXX (Toll Free)</p>{msg}
    <form method="POST">
      <div style="margin-bottom:14px"><label class="lbl">Full Name</label><input class="inp" type="text" name="name" placeholder="Your full name" required></div>
      <div style="margin-bottom:14px"><label class="lbl">Email Address</label><input class="inp" type="email" name="email" placeholder="your@email.com"></div>
      <div style="margin-bottom:14px"><label class="lbl">Subject</label><input class="inp" type="text" name="subject" placeholder="Brief subject"></div>
      <div style="margin-bottom:20px"><label class="lbl">Message</label><textarea class="inp" name="message" rows="5" placeholder="Describe your issue..."></textarea></div>
      <button class="btn btn-p" type="submit">Submit Request</button>
    </form>
  </div>
</div>
{footer()}</body></html>'''

@app.route('/about')
def about():
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — About</title>{CSS}</head><body>
{nav()}
<div class="container" style="padding-top:30px"><div class="card">
  <h2 style="color:#003366;margin-bottom:12px">About SecureBank</h2>
  <p style="color:#555;line-height:1.7;margin-bottom:12px">SecureBank Ltd. is a leading private sector bank in India, established in 1994. With over 2 million customers and 800+ branches, we are committed to world-class banking services.</p>
  <p style="color:#555;line-height:1.7">Regulated by the Reserve Bank of India and insured under DICGC, SecureBank offers savings accounts, fixed deposits, home loans, and investment services.</p>
</div></div>
{footer()}</body></html>'''

@app.route('/register')
def register():
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Register</title>{CSS}</head><body>
{nav()}
<div class="container" style="max-width:480px;padding-top:30px"><div class="card" style="border-top:4px solid #003366">
  <h2 style="color:#003366;margin-bottom:20px">Open New Account</h2>
  <p style="font-size:13px;color:#666;margin-bottom:16px">Please visit your nearest branch with KYC documents or call 1800-XXX-XXXX.</p>
  <a href="/" class="btn btn-p">Back to Home</a>
</div></div>
{footer()}</body></html>'''

@app.route('/forgot')
def forgot():
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Forgot Password</title>{CSS}</head><body>
{nav()}
<div class="container" style="max-width:420px;padding-top:30px"><div class="card">
  <h2 style="color:#003366;margin-bottom:16px">Reset Password</h2>
  <div style="margin-bottom:14px"><label class="lbl">Registered Mobile / Email</label><input class="inp" type="text" placeholder="Enter registered mobile or email"></div>
  <button class="btn btn-p" style="width:100%">Send OTP</button>
</div></div>
{footer()}</body></html>'''

@app.route('/bills')
def bills():
    if not session.get('user'): return redirect('/login')
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>SecureBank — Bills</title>{CSS}</head><body>
{nav(session["user"])}
<div class="container" style="max-width:500px;padding-top:30px"><div class="card">
  <h2 style="color:#003366;margin-bottom:20px">Bill Payments</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <div style="border:1px solid #e0e0e0;padding:20px;text-align:center;cursor:pointer"><div style="font-size:28px;margin-bottom:8px">&#9889;</div><div style="font-size:13px;font-weight:600;color:#003366">Electricity</div></div>
    <div style="border:1px solid #e0e0e0;padding:20px;text-align:center;cursor:pointer"><div style="font-size:28px;margin-bottom:8px">&#128241;</div><div style="font-size:13px;font-weight:600;color:#003366">Mobile Recharge</div></div>
    <div style="border:1px solid #e0e0e0;padding:20px;text-align:center;cursor:pointer"><div style="font-size:28px;margin-bottom:8px">&#127760;</div><div style="font-size:13px;font-weight:600;color:#003366">Broadband</div></div>
    <div style="border:1px solid #e0e0e0;padding:20px;text-align:center;cursor:pointer"><div style="font-size:28px;margin-bottom:8px">&#127968;</div><div style="font-size:13px;font-weight:600;color:#003366">Insurance</div></div>
  </div>
</div></div>
{footer()}</body></html>'''

# ── Admin Routes ───────────────────────────────────────────────────────────────
@app.route('/admin')
def admin_redirect():
    if session.get('acc') != 'admin': return redirect('/login')
    return redirect('/admin/overview')

@app.route('/admin/overview')
def admin_overview():
    if session.get('acc') != 'admin': return redirect('/login')
    active_users = sum(1 for u in ALL_USERS if u['status']=='Active')
    fraud_count  = sum(1 for t in ALL_TXNS if t['flag']=='Fraud')
    flagged = [t for t in ALL_TXNS if t['flag']]
    rows = ''.join([f'''<tr>
      <td style="font-family:monospace;color:#1565c0">{t["id"]}</td>
      <td>{t["date"]}</td><td>{t["from"]}</td><td>{t["to"]}</td>
      <td style="font-weight:600">{t["amount"]}</td>
      <td><span class="badge {'badge-ok' if t['status']=='Success' else 'badge-err'}">{t["status"]}</span></td>
      <td><span class="badge {'badge-err' if t['flag']=='Fraud' else 'badge-warn'}">{t["flag"]}</span></td>
    </tr>''' for t in flagged])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin — Overview</title>{ADMIN_CSS}</head><body>
{admin_nav()}
<div class="layout">{admin_sidebar('overview')}
<div class="content">
  <div class="page-title">Admin Overview</div>
  <div class="stat-grid">
    <div class="stat"><div class="stat-val">{len(ALL_USERS)}</div><div class="stat-lbl">Total Customers</div></div>
    <div class="stat" style="border-top-color:#2e7d32"><div class="stat-val" style="color:#2e7d32">{active_users}</div><div class="stat-lbl">Active Accounts</div></div>
    <div class="stat" style="border-top-color:#c62828"><div class="stat-val" style="color:#c62828">{fraud_count}</div><div class="stat-lbl">Fraud Alerts</div></div>
    <div class="stat" style="border-top-color:#1565c0"><div class="stat-val" style="color:#1565c0">&#8377;17,37,270</div><div class="stat-lbl">Total Deposits</div></div>
  </div>
  <div class="acard">
    <div style="font-size:14px;font-weight:700;color:#1a0533;margin-bottom:14px">&#9888; Flagged Transactions</div>
    <table><thead><tr><th>TXN ID</th><th>Date</th><th>From</th><th>To</th><th>Amount</th><th>Status</th><th>Flag</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>
</div></div></body></html>'''

@app.route('/admin/users')
def admin_users():
    if session.get('acc') != 'admin': return redirect('/login')
    search = request.args.get('q','')
    users = [u for u in ALL_USERS if search.lower() in u['name'].lower() or search.lower() in u['username'].lower()] if search else ALL_USERS
    rows = ''.join([f'''<tr>
      <td style="font-family:monospace;color:#1565c0">{u["id"]}</td>
      <td><strong>{u["name"]}</strong><br><span style="font-size:11px;color:#999">{u["username"]}</span></td>
      <td style="font-family:monospace">{u["acc"]}</td>
      <td style="font-weight:600;color:#1a0533">{u["balance"]}</td>
      <td><span class="badge {'badge-ok' if u['status']=='Active' else 'badge-err' if u['status']=='Locked' else 'badge-warn'}">{u["status"]}</span></td>
      <td><span class="badge {'badge-ok' if u['kyc']=='Verified' else 'badge-err' if u['kyc']=='Failed' else 'badge-warn'}">{u["kyc"]}</span></td>
      <td style="font-size:12px;color:#888">{u["joined"]}</td>
      <td style="display:flex;gap:6px;">
        <form method="POST" action="/admin/block_user"><input type="hidden" name="uid" value="{u["id"]}"><button class="btn btn-r">Suspend</button></form>
        <form method="POST" action="/admin/unblock_user"><input type="hidden" name="uid" value="{u["id"]}"><button class="btn btn-g">Activate</button></form>
      </td>
    </tr>''' for u in users])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin — Users</title>{ADMIN_CSS}</head><body>
{admin_nav()}
<div class="layout">{admin_sidebar('users')}
<div class="content">
  <div class="page-title">User Management</div>
  <div class="acard">
    <form action="/admin/users" method="GET" style="display:flex;gap:10px;margin-bottom:16px;">
      <input class="inp" name="q" placeholder="Search by name or username..." value="{search}" style="width:300px">
      <button class="btn btn-p" type="submit">Search</button>
    </form>
    <table><thead><tr><th>ID</th><th>Customer</th><th>Account</th><th>Balance</th><th>Status</th><th>KYC</th><th>Joined</th><th>Actions</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>
</div></div></body></html>'''

@app.route('/admin/block_user', methods=['POST'])
def admin_block_user():
    if session.get('acc') != 'admin': return redirect('/login')
    uid = request.form.get('uid')
    for u in ALL_USERS:
        if u['id'] == uid: u['status'] = 'Suspended'
    return redirect('/admin/users')

@app.route('/admin/unblock_user', methods=['POST'])
def admin_unblock_user():
    if session.get('acc') != 'admin': return redirect('/login')
    uid = request.form.get('uid')
    for u in ALL_USERS:
        if u['id'] == uid: u['status'] = 'Active'
    return redirect('/admin/users')

@app.route('/admin/transactions')
def admin_transactions():
    if session.get('acc') != 'admin': return redirect('/login')
    filt = request.args.get('filter','all')
    txns = ALL_TXNS if filt=='all' else [t for t in ALL_TXNS if t['flag']==filt or t['status']==filt]
    rows = ''.join([f'''<tr>
      <td style="font-family:monospace;color:#1565c0">{t["id"]}</td>
      <td style="font-size:12px;color:#888">{t["date"]}</td>
      <td>{t["from"]}</td><td>{t["to"]}</td>
      <td style="font-weight:600">{t["amount"]}</td>
      <td><span class="badge badge-info">{t["type"]}</span></td>
      <td><span class="badge {'badge-ok' if t['status']=='Success' else 'badge-err'}">{t["status"]}</span></td>
      <td>{"<span class='badge " + ("badge-err" if t["flag"]=="Fraud" else "badge-warn") + "'>" + t["flag"] + "</span>" if t["flag"] else "-"}</td>
    </tr>''' for t in txns])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin — Transactions</title>{ADMIN_CSS}</head><body>
{admin_nav()}
<div class="layout">{admin_sidebar('transactions')}
<div class="content">
  <div class="page-title">Transaction Monitor</div>
  <div class="acard">
    <div style="display:flex;gap:8px;margin-bottom:16px;">
      <a href="?filter=all" class="btn {'btn-p' if filt=='all' else 'btn-y'}">All</a>
      <a href="?filter=Fraud" class="btn {'btn-p' if filt=='Fraud' else 'btn-r'}">Fraud</a>
      <a href="?filter=Suspicious" class="btn {'btn-p' if filt=='Suspicious' else 'btn-y'}">Suspicious</a>
      <a href="?filter=Blocked" class="btn {'btn-p' if filt=='Blocked' else 'btn-r'}">Blocked</a>
    </div>
    <table><thead><tr><th>TXN ID</th><th>Date</th><th>From</th><th>To</th><th>Amount</th><th>Type</th><th>Status</th><th>Flag</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>
</div></div></body></html>'''

@app.route('/admin/fraud')
def admin_fraud():
    if session.get('acc') != 'admin': return redirect('/login')
    fraud_txns   = [t for t in ALL_TXNS  if t['flag']]
    locked_users = [u for u in ALL_USERS if u['status'] in ('Suspended','Locked')]
    txn_rows = ''.join([f'<tr><td style="font-family:monospace;color:#c62828">{t["id"]}</td><td>{t["date"]}</td><td>{t["from"]}</td><td>{t["to"]}</td><td style="font-weight:600">{t["amount"]}</td><td><span class="badge badge-err">{t["flag"]}</span></td></tr>' for t in fraud_txns])
    usr_rows = ''.join([f'<tr><td>{u["name"]}</td><td style="font-family:monospace">{u["acc"]}</td><td><span class="badge badge-err">{u["status"]}</span></td><td>{u["kyc"]}</td></tr>' for u in locked_users])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin — Fraud</title>{ADMIN_CSS}</head><body>
{admin_nav()}
<div class="layout">{admin_sidebar('fraud')}
<div class="content">
  <div class="page-title">&#9888; Fraud Alerts</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <div class="stat" style="border-top-color:#c62828"><div class="stat-val" style="color:#c62828">{len(fraud_txns)}</div><div class="stat-lbl">Flagged Transactions</div></div>
    <div class="stat" style="border-top-color:#f57f17"><div class="stat-val" style="color:#f57f17">{len(locked_users)}</div><div class="stat-lbl">Suspended / Locked Users</div></div>
  </div>
  <div class="acard">
    <div style="font-size:14px;font-weight:700;color:#c62828;margin-bottom:12px">Flagged Transactions</div>
    <table><thead><tr><th>TXN ID</th><th>Date</th><th>From</th><th>To</th><th>Amount</th><th>Flag</th></tr></thead><tbody>{txn_rows}</tbody></table>
  </div>
  <div class="acard">
    <div style="font-size:14px;font-weight:700;color:#f57f17;margin-bottom:12px">Restricted Accounts</div>
    <table><thead><tr><th>Customer</th><th>Account</th><th>Status</th><th>KYC</th></tr></thead><tbody>{usr_rows}</tbody></table>
  </div>
</div></div></body></html>'''

@app.route('/admin/system')
def admin_system():
    if session.get('acc') != 'admin': return redirect('/login')
    q = request.args.get('q','')
    qresult = f'<div style="margin-top:12px;padding:10px;background:#f8f9fa;border:1px solid #e0e0e0;font-family:monospace;font-size:12px;">Query: <strong>{q}</strong><br>Result: Access restricted by WAF.</div>' if q else ''
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin — System</title>{ADMIN_CSS}</head><body>
{admin_nav()}
<div class="layout">{admin_sidebar('system')}
<div class="content">
  <div class="page-title">System Settings</div>
  <div class="acard">
    <div style="font-size:14px;font-weight:700;color:#1a0533;margin-bottom:16px">Security Settings</div>
    <div style="display:grid;gap:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border:1px solid #e0e0e0;"><div><div style="font-size:13px;font-weight:600">Two-Factor Authentication</div><div style="font-size:12px;color:#888">Require OTP for all logins</div></div><span class="badge badge-ok">Enabled</span></div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border:1px solid #e0e0e0;"><div><div style="font-size:13px;font-weight:600">Transaction Limit</div><div style="font-size:12px;color:#888">Max single transfer limit</div></div><span style="font-weight:700;color:#1a0533">&#8377;2,00,000</span></div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border:1px solid #e0e0e0;"><div><div style="font-size:13px;font-weight:600">Session Timeout</div><div style="font-size:12px;color:#888">Auto logout after inactivity</div></div><span style="font-weight:700;color:#1a0533">15 minutes</span></div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;border:1px solid #e0e0e0;"><div><div style="font-size:13px;font-weight:600">IP Whitelist</div><div style="font-size:12px;color:#888">Admin access restriction</div></div><span class="badge badge-warn">Disabled</span></div>
    </div>
  </div>
  <div class="acard">
    <div style="font-size:14px;font-weight:700;color:#1a0533;margin-bottom:16px">Database Query (Admin Only)</div>
    <form action="/admin/system" method="GET" style="display:flex;gap:10px;">
      <input class="inp" name="q" placeholder="SELECT * FROM users WHERE id=..." style="flex:1" value="{q}">
      <button class="btn btn-p" type="submit">Execute</button>
    </form>{qresult}
  </div>
</div></div></body></html>'''

@app.route('/admin/logs')
def admin_logs():
    if session.get('acc') != 'admin': return redirect('/login')
    logs = [
        {'time':'12 Mar 2026 19:34','action':'Login',     'user':'admin',   'ip':'192.168.0.8',   'status':'Success'},
        {'time':'12 Mar 2026 19:12','action':'Block User','user':'admin',   'ip':'192.168.0.8',   'status':'Success'},
        {'time':'12 Mar 2026 18:45','action':'Login',     'user':'user',    'ip':'103.21.244.12', 'status':'Success'},
        {'time':'12 Mar 2026 18:30','action':'Transfer',  'user':'user',    'ip':'103.21.244.12', 'status':'Success'},
        {'time':'12 Mar 2026 17:22','action':'Login',     'user':'unknown', 'ip':'45.33.32.156',  'status':'Failed'},
        {'time':'12 Mar 2026 17:21','action':'Login',     'user':'admin',   'ip':'45.33.32.156',  'status':'Failed'},
        {'time':'12 Mar 2026 17:20','action':'Login',     'user':'admin',   'ip':'45.33.32.156',  'status':'Failed'},
    ]
    rows = ''.join([f'<tr><td style="font-size:12px;color:#888">{l["time"]}</td><td>{l["action"]}</td><td style="font-family:monospace">{l["user"]}</td><td style="font-family:monospace;color:#1565c0">{l["ip"]}</td><td><span class="badge {"badge-ok" if l["status"]=="Success" else "badge-err"}">{l["status"]}</span></td></tr>' for l in logs])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin — Audit Logs</title>{ADMIN_CSS}</head><body>
{admin_nav()}
<div class="layout">{admin_sidebar('logs')}
<div class="content">
  <div class="page-title">Audit Logs</div>
  <div class="acard">
    <table><thead><tr><th>Timestamp</th><th>Action</th><th>User</th><th>IP Address</th><th>Status</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>
</div></div></body></html>'''

# ── 404 & Main ─────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>404</title>{CSS}</head><body>
{nav()}<div style="text-align:center;padding:80px 20px">
  <h1 style="font-size:64px;color:#003366;font-weight:800">404</h1>
  <p style="font-size:18px;color:#666;margin:12px 0">Page not found</p>
  <a href="/" style="color:#003366">Return to Home</a>
</div>{footer()}</body></html>''', 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7777, debug=False)