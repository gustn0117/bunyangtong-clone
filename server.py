import http.server
import os
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        # Parse the URL - keep everything as part of the file path
        # Don't strip query parameters since they're part of the filename
        path = urllib.parse.unquote(path)
        # Remove leading slash
        path = path.lstrip('/')
        return os.path.join(ROOT, path)

    def do_GET(self):
        # Redirect root to site folder
        if self.path == '/' or self.path == '':
            self.send_response(301)
            self.send_header('Location', '/xn--4k0bm4xt7at1qcucmyumnb0xe.kr/')
            self.end_headers()
            return

        # The raw path includes & which might be in filenames
        raw = urllib.parse.unquote(self.path).lstrip('/')
        full_path = os.path.join(ROOT, raw)

        if os.path.isfile(full_path):
            self.send_file(full_path)
        elif os.path.isdir(full_path):
            # Try index.html
            index = os.path.join(full_path, 'index.html')
            if os.path.isfile(index):
                self.send_file(index)
            else:
                super().do_GET()
        else:
            super().do_GET()

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '3000'))
    server = http.server.HTTPServer(('', port), Handler)
    print(f'Serving at http://localhost:{port}/xn--4k0bm4xt7at1qcucmyumnb0xe.kr/')
    server.serve_forever()
