import http.server
import os
import urllib.parse
import json
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'data')
SUBMISSIONS_FILE = os.path.join(DATA_DIR, 'submissions.json')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'bunyang2026!')

os.makedirs(DATA_DIR, exist_ok=True)

def load_submissions():
    if os.path.isfile(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_submission(data):
    submissions = load_submissions()
    data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
    data['id'] = int(time.time() * 1000)
    submissions.insert(0, data)
    with open(SUBMISSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        path = urllib.parse.unquote(path)
        path = path.lstrip('/')
        return os.path.join(ROOT, path)

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.send_response(301)
            self.send_header('Location', '/xn--4k0bm4xt7at1qcucmyumnb0xe.kr/')
            self.end_headers()
            return

        if self.path == '/admin':
            self.serve_admin_page()
            return

        if self.path == '/api/submissions':
            self.serve_submissions_api()
            return

        raw = urllib.parse.unquote(self.path).lstrip('/')
        full_path = os.path.join(ROOT, raw)

        if os.path.isfile(full_path):
            self.send_file(full_path)
        elif os.path.isdir(full_path):
            index = os.path.join(full_path, 'index.html')
            if os.path.isfile(index):
                self.send_file(index)
            else:
                super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/submit':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                # Honeypot check
                honeypot_fields = ['website', 'company', 'message', 'subject',
                                   'title', 'description', 'feedback', 'notes',
                                   'details', 'remarks', 'comments']
                is_spam = any(data.get(f) for f in honeypot_fields)
                if not is_spam:
                    save_submission({
                        'site_name': data.get('현장명', ''),
                        'name': data.get('이름', ''),
                        'phone': data.get('전화번호', ''),
                    })
                self.send_json(200, {'success': True})
            except Exception:
                self.send_json(400, {'error': 'Invalid request'})
            return

        if self.path == '/api/delete':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                if data.get('password') != ADMIN_PASSWORD:
                    self.send_json(401, {'error': 'Unauthorized'})
                    return
                target_id = data.get('id')
                submissions = load_submissions()
                submissions = [s for s in submissions if s.get('id') != target_id]
                with open(SUBMISSIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(submissions, f, ensure_ascii=False, indent=2)
                self.send_json(200, {'success': True})
            except Exception:
                self.send_json(400, {'error': 'Invalid request'})
            return

        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def serve_submissions_api(self):
        pw = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('password', [None])[0]
        if self.path.startswith('/api/submissions'):
            query = urllib.parse.urlparse(self.path).query
            pw = urllib.parse.parse_qs(query).get('password', [None])[0]
        if pw != ADMIN_PASSWORD:
            self.send_json(401, {'error': 'Unauthorized'})
            return
        submissions = load_submissions()
        self.send_json(200, submissions)

    def serve_admin_page(self):
        html = ADMIN_HTML.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html))
        self.end_headers()
        self.wfile.write(html)

    def send_file(self, filepath):
        ext = os.path.splitext(filepath.split('@')[0])[1].lower()
        content_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.mjs': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
            '.woff2': 'font/woff2',
            '.woff': 'font/woff',
            '.ttf': 'font/ttf',
            '.json': 'application/json',
            '.ico': 'image/x-icon',
        }
        ct = content_types.get(ext, 'application/octet-stream')
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_error(404)

ADMIN_HTML = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>관리자 - 문의 내역</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e0e0e0; min-height: 100vh; }
.login-wrap, .admin-wrap { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
h1 { font-size: 24px; margin-bottom: 30px; color: #fff; }
.login-box { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 40px; max-width: 400px; margin: 100px auto; }
.login-box h2 { margin-bottom: 20px; color: #fff; }
.login-box input { width: 100%; padding: 12px 16px; background: #0a0a0a; border: 1px solid #333; border-radius: 8px; color: #fff; font-size: 16px; margin-bottom: 16px; }
.login-box button { width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
.login-box button:hover { background: #1d4ed8; }
.error { color: #ef4444; font-size: 14px; margin-bottom: 12px; display: none; }
.stats { display: flex; gap: 16px; margin-bottom: 24px; }
.stat-card { background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 16px 24px; flex: 1; }
.stat-card .label { font-size: 13px; color: #888; }
.stat-card .value { font-size: 28px; font-weight: 700; color: #fff; margin-top: 4px; }
.card { background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 20px; margin-bottom: 12px; }
.card .meta { font-size: 13px; color: #666; margin-bottom: 12px; }
.card .fields { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.card .field-label { font-size: 12px; color: #888; margin-bottom: 2px; }
.card .field-value { font-size: 16px; color: #fff; font-weight: 500; }
.card .actions { margin-top: 12px; text-align: right; }
.btn-delete { background: none; border: 1px solid #ef4444; color: #ef4444; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-delete:hover { background: #ef4444; color: #fff; }
.empty { text-align: center; color: #666; padding: 60px 0; font-size: 16px; }
.phone-link { color: #60a5fa; text-decoration: none; }
.phone-link:hover { text-decoration: underline; }
@media (max-width: 600px) { .card .fields { grid-template-columns: 1fr; } }
</style>
</head>
<body>

<div class="login-wrap" id="loginSection">
  <div class="login-box">
    <h2>관리자 로그인</h2>
    <p class="error" id="loginError">비밀번호가 올바르지 않습니다.</p>
    <input type="password" id="pwInput" placeholder="비밀번호" autofocus>
    <button onclick="login()">로그인</button>
  </div>
</div>

<div class="admin-wrap" id="adminSection" style="display:none">
  <h1>문의 내역</h1>
  <div class="stats">
    <div class="stat-card">
      <div class="label">총 문의</div>
      <div class="value" id="totalCount">0</div>
    </div>
    <div class="stat-card">
      <div class="label">오늘</div>
      <div class="value" id="todayCount">0</div>
    </div>
  </div>
  <div id="list"></div>
</div>

<script>
let password = '';

function login() {
  password = document.getElementById('pwInput').value;
  fetch('/api/submissions?password=' + encodeURIComponent(password))
    .then(r => { if (!r.ok) throw new Error(); return r.json(); })
    .then(data => {
      document.getElementById('loginSection').style.display = 'none';
      document.getElementById('adminSection').style.display = 'block';
      render(data);
    })
    .catch(() => {
      document.getElementById('loginError').style.display = 'block';
    });
}

document.getElementById('pwInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') login();
});

function render(data) {
  document.getElementById('totalCount').textContent = data.length;
  const today = new Date().toISOString().slice(0, 10);
  document.getElementById('todayCount').textContent = data.filter(d => d.timestamp && d.timestamp.startsWith(today)).length;
  const list = document.getElementById('list');
  if (data.length === 0) {
    list.innerHTML = '<div class="empty">아직 문의가 없습니다.</div>';
    return;
  }
  list.innerHTML = data.map(d => `
    <div class="card">
      <div class="meta">${d.timestamp || ''}</div>
      <div class="fields">
        <div><div class="field-label">현장명</div><div class="field-value">${esc(d.site_name)}</div></div>
        <div><div class="field-label">이름</div><div class="field-value">${esc(d.name)}</div></div>
        <div><div class="field-label">전화번호</div><div class="field-value"><a class="phone-link" href="tel:${esc(d.phone)}">${esc(d.phone)}</a></div></div>
      </div>
      <div class="actions"><button class="btn-delete" onclick="del(${d.id})">삭제</button></div>
    </div>
  `).join('');
}

function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

function del(id) {
  if (!confirm('삭제하시겠습니까?')) return;
  fetch('/api/delete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id, password})
  }).then(() => location.reload());
}
</script>
</body>
</html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '3000'))
    server = http.server.HTTPServer(('', port), Handler)
    print(f'Serving at http://localhost:{port}/xn--4k0bm4xt7at1qcucmyumnb0xe.kr/')
    server.serve_forever()
