from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import subprocess, re, json, os, urllib.request
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

app = Flask(__name__)
app.secret_key = 'piwaf-secret-2026'

ADMIN_USER = 'admin'
ADMIN_PASS = 'admin'
BLOCKED_IPS_FILE = '/etc/piwaf/blocked_ips.json'
BLOCKED_COUNTRIES_FILE = '/etc/piwaf/blocked_countries.json'
CUSTOM_RULES_FILE = '/etc/piwaf/custom_rules.conf'
MODSEC_CUSTOM_INCLUDE = '/usr/local/nginx/conf/custom_rules.conf'
GEO_CACHE_FILE = '/etc/piwaf/geo_cache.json'
NGINX_ACCESS_LOG = '/usr/local/nginx/logs/access.log'
os.makedirs('/etc/piwaf', exist_ok=True)

def load_json(path, default):
    try:
        with open(path) as f: return json.load(f)
    except: return default

def save_json(path, data):
    with open(path, 'w') as f: json.dump(data, f)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def parse_audit_log():
    attacks, timeline, sev_counts = [], defaultdict(int), {'HIGH':0,'MEDIUM':0,'LOW':0}
    attack_types = defaultdict(int)
    rule_hits = defaultdict(lambda:{'count':0,'desc':'','file':'','line':''})
    source_ips = defaultdict(int)
    dest_uris = defaultdict(int)
    total_requests = 0
    try:
        with open('/var/log/modsec_audit.log') as f:
            content = f.read()
        cur_ip = cur_time = cur_method = cur_uri = cur_ua = None
        cur_xff = None
        for line in content.split('\n'):
            m = re.search(r'\[(\d+/\w+/\d+:\d+:\d+:\d+)[^\]]*\]\s+\S+\s+(\S+)\s+\d+\s+\S+\s+\d+', line)
            if m:
                cur_time = m.group(1)
                cur_ip = m.group(2)
                cur_xff = None
                total_requests += 1
            xff = re.match(r'^X-Forwarded-For:\s+(.*)', line, re.IGNORECASE)
            if xff:
                real_ip = xff.group(1).strip().split(',')[0].strip()
                if real_ip: cur_xff = real_ip
            req = re.match(r'^(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+(\S+)', line)
            if req: cur_method = req.group(1); cur_uri = req.group(2)
            ua = re.match(r'^User-Agent:\s+(.*)', line)
            if ua: cur_ua = ua.group(1)
            if 'ModSecurity: Access denied' in line and cur_ip:
                msg_m  = re.search(r'\[msg "([^"]+)"\]', line)
                sev_m  = re.search(r'\[severity "(\d+)"\]', line)
                id_m   = re.search(r'\[id "(\d+)"\]', line)
                file_m = re.search(r'\[file "([^"]+)"\]', line)
                line_m = re.search(r'\[line "([^"]+)"\]', line)
                msg    = msg_m.group(1) if msg_m else 'Attack detected'
                sev_n  = int(sev_m.group(1)) if sev_m else 5
                rule_id= id_m.group(1) if id_m else '000000'
                rule_file = os.path.basename(file_m.group(1)) if file_m else '-'
                sev = 'HIGH' if sev_n<=2 else ('MEDIUM' if sev_n<=4 else 'LOW')
                sev_counts[sev] += 1
                if 'sqli' in line.lower() or 'sql' in msg.lower(): atype='SQL Injection'
                elif 'xss' in line.lower() or 'cross-site' in msg.lower(): atype='XSS'
                elif 'traversal' in msg.lower(): atype='LFI/Path Traversal'
                elif 'rfi' in msg.lower(): atype='RFI'
                elif 'command' in msg.lower() or 'shell' in msg.lower(): atype='Command Injection'
                elif 'scanner' in msg.lower(): atype='Scanner'
                elif 'anomaly' in msg.lower(): atype='Anomaly'
                else: atype='Other'
                attack_types[atype] += 1
                rule_hits[rule_id]['count'] += 1
                rule_hits[rule_id]['desc'] = msg
                rule_hits[rule_id]['file'] = rule_file
                rule_hits[rule_id]['line'] = line_m.group(1) if line_m else '-'
                real = cur_xff if cur_xff and cur_ip in ('127.0.0.1','::1') else cur_ip
                cur_ip = real
                source_ips[cur_ip] += 1
                if cur_uri: dest_uris[cur_uri] += 1
                try:
                    t = datetime.strptime(cur_time, '%d/%b/%Y:%H:%M:%S')
                    timeline[t.strftime('%H:00')] += 1
                except: pass
                attacks.append({'time':cur_time,'ip':cur_ip,'method':cur_method or 'GET',
                                'uri':cur_uri or '/','ua':cur_ua or '-','msg':msg,
                                'severity':sev,'type':atype,'rule':rule_id,'file':rule_file})
    except: pass
    now = datetime.now()
    tl = [{'hour':(now-timedelta(hours=i)).strftime('%H:00'),
            'count':timeline.get((now-timedelta(hours=i)).strftime('%H:00'),0)} for i in range(23,-1,-1)]
    return {
        'attacks': attacks[-200:][::-1], 'total': len(attacks),
        'total_requests': max(total_requests, len(attacks)),
        'timeline': tl, 'severity': sev_counts,
        'attack_types': dict(attack_types),
        'top_rules': sorted([{'id':k,'count':v['count'],'desc':v['desc'],'file':v['file'],'line':v['line']}
                              for k,v in rule_hits.items()], key=lambda x:x['count'], reverse=True)[:20],
        'top_ips': sorted([{'ip':k,'count':v} for k,v in source_ips.items()], key=lambda x:x['count'], reverse=True)[:10],
        'top_uris': sorted([{'uri':k,'count':v} for k,v in dest_uris.items()], key=lambda x:x['count'], reverse=True)[:10]
    }

def parse_normal_traffic():
    """Parse nginx access.log — skip 403 blocked requests, show only normal traffic"""
    requests_list = []
    try:
        with open(NGINX_ACCESS_LOG) as f:
            lines = f.readlines()[-500:]
        for line in lines:
            # Nginx combined log format: IP - - [time] "METHOD URI PROTO" STATUS SIZE "ref" "ua"
            m = re.match(r'(\S+)\s+-\s+-\s+\[([^\]]+)\]\s+"(\w+)\s+(\S+)\s+\S+"\s+(\d+)\s+(\d+)\s+"[^"]*"\s+"([^"]*)"', line)
            if not m:
                # Try without user agent
                m = re.match(r'(\S+)\s+-\s+-\s+\[([^\]]+)\]\s+"(\w+)\s+(\S+)\s+\S+"\s+(\d+)\s+(\d+)', line)
                if not m: continue
                ip,time_str,method,uri,status,size = m.groups()
                ua = '-'
            else:
                ip,time_str,method,uri,status,size,ua = m.groups()
            if status == '403': continue  # skip WAF blocked ones
            requests_list.append({
                'ip':ip, 'time':time_str, 'method':method,
                'uri':uri[:80], 'status':status, 'size':size, 'ua':ua
            })
    except: pass
    return {
        'requests': requests_list[-200:][::-1],
        'total': len(requests_list)
    }

def get_fail2ban_stats():
    try:
        r = subprocess.run(['fail2ban-client','status','modsecurity'], capture_output=True, text=True)
        tb = re.search(r'Total banned:\s*(\d+)', r.stdout)
        cb = re.search(r'Currently banned:\s*(\d+)', r.stdout)
        bi = re.search(r'Banned IP list:\s*(.*)', r.stdout)
        ips = bi.group(1).strip().split() if bi and bi.group(1).strip() else []
        return {'total_banned':int(tb.group(1)) if tb else 0,
                'currently_banned':int(cb.group(1)) if cb else 0, 'banned_ips':ips}
    except: return {'total_banned':0,'currently_banned':0,'banned_ips':[]}

def svc_status(name):
    r = subprocess.run(['systemctl','is-active',name], capture_output=True, text=True)
    return 'RUNNING' if r.stdout.strip()=='active' else 'STOPPED'

def get_all_rules():
    rules = []
    rules_dir = '/usr/local/nginx/conf/coreruleset/rules'
    try:
        for fname in sorted(os.listdir(rules_dir)):
            if not fname.endswith('.conf'): continue
            path = os.path.join(rules_dir, fname)
            with open(path) as f: content = f.read()
            for m in re.finditer(r'SecRule\s+(\S+)\s+"([^"]+)"\s*\\\s*\n\s*"([^"]*)"', content):
                options = m.group(3)
                id_m  = re.search(r'id:(\d+)', options)
                msg_m = re.search(r"msg:'([^']+)'", options)
                sev_m = re.search(r"severity:'(\w+)'", options)
                tag_m = re.search(r"tag:'([^']+)'", options)
                phase_m = re.search(r'phase:(\d+)', options)
                action_m = re.search(r'\b(deny|pass|drop|allow)\b', options)
                if not id_m: continue
                rules.append({
                    'id': id_m.group(1), 'file': fname,
                    'variable': m.group(1), 'operator': m.group(2)[:50],
                    'msg': msg_m.group(1) if msg_m else m.group(2)[:50],
                    'severity': sev_m.group(1) if sev_m else 'INFO',
                    'tag': tag_m.group(1) if tag_m else '',
                    'phase': phase_m.group(1) if phase_m else '-',
                    'action': (action_m.group(1).upper() if action_m else 'BLOCK'),
                    'enabled': True
                })
    except: pass
    try:
        with open(CUSTOM_RULES_FILE) as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'): continue
                id_m = re.search(r'id:(\d+)', line)
                msg_m = re.search(r"msg:'([^']+)'", line)
                rules.append({
                    'id': id_m.group(1) if id_m else f'custom-{i}',
                    'file': 'CUSTOM', 'variable': 'CUSTOM', 'operator': '',
                    'msg': msg_m.group(1) if msg_m else line[:60],
                    'severity': 'CRITICAL', 'tag': 'custom', 'phase': '2',
                    'action': 'BLOCK', 'enabled': True
                })
    except: pass
    return rules

# ── Routes ────────────────────────────────────────────────────
@app.route('/')
@login_required
def dashboard():
    d = parse_audit_log(); f = get_fail2ban_stats()
    return render_template('base.html', page='dashboard',
        log=d, f2b=f, nginx=svc_status('nginx-waf'), fail2ban=svc_status('fail2ban'))

@app.route('/events')
@login_required
def events():
    tab = request.args.get('tab', 'attack')
    return render_template('base.html', page='events',
        log=parse_audit_log(),
        normal=parse_normal_traffic(),
        active_tab=tab)

@app.route('/security')
@login_required
def security():
    return render_template('base.html', page='security',
        rules=get_all_rules(),
        blocked_ips=load_json(BLOCKED_IPS_FILE, []),
        blocked_countries=load_json(BLOCKED_COUNTRIES_FILE, []),
        f2b=get_fail2ban_stats(),
        custom_rules=open(CUSTOM_RULES_FILE).read() if os.path.exists(CUSTOM_RULES_FILE) else '')

@app.route('/wafstatus')
@login_required
def wafstatus():
    d = parse_audit_log(); f = get_fail2ban_stats()
    return render_template('base.html', page='wafstatus',
        log=d, f2b=f, nginx=svc_status('nginx-waf'),
        fail2ban=svc_status('fail2ban'), rules=get_all_rules())

# ── API ───────────────────────────────────────────────────────
@app.route('/api/block_ip', methods=['POST'])
@login_required
def block_ip():
    ip = request.form.get('ip','').strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip): return 'Invalid IP', 400
    ips = load_json(BLOCKED_IPS_FILE, [])
    if ip not in ips:
        ips.append(ip)
        save_json(BLOCKED_IPS_FILE, ips)
        subprocess.run(['iptables','-I','INPUT','-s',ip,'-j','DROP'])
    return redirect(url_for('security'))

@app.route('/api/unblock_ip', methods=['POST'])
@login_required
def unblock_ip():
    ip = request.form.get('ip','').strip()
    ips = load_json(BLOCKED_IPS_FILE, [])
    if ip in ips:
        ips.remove(ip); save_json(BLOCKED_IPS_FILE, ips)
        subprocess.run(['iptables','-D','INPUT','-s',ip,'-j','DROP'])
    subprocess.run(['fail2ban-client','set','modsecurity','unbanip',ip], capture_output=True)
    return redirect(url_for('security'))

@app.route('/api/block_country', methods=['POST'])
@login_required
def block_country():
    c = request.form.get('country','').strip()
    cs = load_json(BLOCKED_COUNTRIES_FILE, [])
    if c and c not in cs: cs.append(c); save_json(BLOCKED_COUNTRIES_FILE, cs)
    return redirect(url_for('security') + '#geoblocking')

@app.route('/api/unblock_country', methods=['POST'])
@login_required
def unblock_country():
    c = request.form.get('country','').strip()
    cs = load_json(BLOCKED_COUNTRIES_FILE, [])
    if c in cs: cs.remove(c); save_json(BLOCKED_COUNTRIES_FILE, cs)
    return redirect(url_for('security') + '#geoblocking')

@app.route('/api/add_rule', methods=['POST'])
@login_required
def add_rule():
    rule_text = request.form.get('rule','').strip()
    if not rule_text.startswith('SecRule'):
        return 'Rule must start with SecRule', 400
    with open(CUSTOM_RULES_FILE, 'a') as f:
        f.write(rule_text + '\n')
    try:
        with open(CUSTOM_RULES_FILE) as f: content = f.read()
        with open(MODSEC_CUSTOM_INCLUDE, 'w') as f: f.write(content)
        modsec_conf = '/usr/local/nginx/conf/modsecurity.conf'
        with open(modsec_conf) as f: mc = f.read()
        inc = f'Include {MODSEC_CUSTOM_INCLUDE}'
        if inc not in mc:
            with open(modsec_conf, 'a') as f: f.write(f'\n{inc}\n')
        test = subprocess.run(['/usr/local/nginx/sbin/nginx','-t'], capture_output=True, text=True)
        if test.returncode == 0:
            subprocess.run(['/usr/local/nginx/sbin/nginx','-s','reload'])
        else:
            with open(CUSTOM_RULES_FILE,'r') as f: lines=f.readlines()
            with open(CUSTOM_RULES_FILE,'w') as f: f.writelines(lines[:-1])
            return f'Rule error: {test.stderr}', 400
    except Exception as e:
        return str(e), 500
    return redirect(url_for('security') + '#rules')

@app.route('/api/restart_nginx', methods=['POST'])
@login_required
def restart_nginx():
    result = subprocess.run(['systemctl','restart','nginx-waf'], capture_output=True, text=True)
    return jsonify({'success': result.returncode==0, 'output': result.stdout+result.stderr})

@app.route('/api/test_waf', methods=['POST'])
@login_required
def test_waf():
    tests = [
        ('SQL Injection','http://localhost/?id=1%27%20OR%20%271%27%3D%271'),
        ('XSS','http://localhost/?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E'),
        ('Path Traversal','http://localhost/?file=../../etc/passwd'),
        ('Command Injection','http://localhost/?cmd=%3Bls%20-la'),
    ]
    results = []
    for name, url in tests:
        try:
            r = subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','-m','3',url],
                               capture_output=True, text=True)
            code = r.stdout.strip()
            results.append({'test':name,'code':code,'blocked':code=='403'})
        except:
            results.append({'test':name,'code':'ERR','blocked':False})
    return jsonify({'results':results})

# ── GeoIP Cache Route ─────────────────────────────────────────
@app.route('/api/geoip')
@login_required
def geoip():
    ip = request.args.get('ip', '').strip()
    if not ip:
        return jsonify({'error': 'no ip'}), 400
    if ip == '127.0.0.1' or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
        return jsonify({'lat': 12.97, 'lon': 77.59, 'country': 'Local/LAN', 'local': True})
    cache = load_json(GEO_CACHE_FILE, {})
    if ip in cache:
        return jsonify(cache[ip])
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,lat,lon,country,city'
        req = urllib.request.Request(url, headers={'User-Agent': 'PiWAF/1.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        if data.get('status') == 'success':
            result = {'lat': data['lat'], 'lon': data['lon'],
                      'country': data.get('country', ''), 'city': data.get('city', ''), 'local': False}
            cache[ip] = result
            save_json(GEO_CACHE_FILE, cache)
            return jsonify(result)
        else:
            return jsonify({'error': 'not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)