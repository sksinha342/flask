import os
import importlib
import io
from flask import Flask, render_template, send_file, abort

app = Flask(__name__)

# -----------------------------------------
# Serve temporary QR images (auto delete)
# -----------------------------------------
@app.route('/temp_qr/<filename>')
def serve_temp_qr(filename):
    safe_name = os.path.basename(filename)  # Prevent directory traversal
    data_dir = os.path.join(os.path.dirname(__file__), 'static', 'Data')
    path = os.path.join(data_dir, safe_name)
    if not os.path.exists(path):
        return abort(404)
    try:
        with open(path, 'rb') as f:
            content = f.read()
        # Delete file after reading
        try:
            os.remove(path)
        except Exception:
            pass
        return send_file(io.BytesIO(content), mimetype='image/jpeg')
    except Exception as e:
        print("Error serving temp qr:", e)
        return abort(500)

# -----------------------------------------
# Auto-load pages from /pages directory
# -----------------------------------------
PAGES_DIR = os.path.join(os.path.dirname(__file__), 'pages')
pages = {}

for file in os.listdir(PAGES_DIR):
    if file.endswith('.py') and not file.startswith('__'):
        module_name = file[:-3]
        module_path = f'pages.{module_name}'
        try:
            mod = importlib.import_module(module_path)
            # each page must define: page_title, page_description, image_path, render_page()
            if hasattr(mod, 'page_title') and hasattr(mod, 'render_page'):
                pages[module_name] = {
                    'title': getattr(mod, 'page_title', module_name),
                    'description': getattr(mod, 'page_description', 'No description available.'),
                    'image': getattr(mod, 'image_path', '/static/default.jpg'),
                    'module': mod
                }
        except Exception as e:
            print(f"⚠️ Error loading {module_name}: {e}")

# -----------------------------------------
# Home route — shows all pages
# -----------------------------------------
@app.route('/qr1')
def qr1():
    return render_template('qr.html',pages=pages)
@app.route('/')
def home():
    return render_template('index.html', pages=pages)

# -----------------------------------------
# Dynamic route creation (FIXED version)
# -----------------------------------------
def make_route(mod):
    def route_func():
        return mod.render_page()
    return route_func

for name, info in pages.items():
    app.add_url_rule(f'/{name}', name, make_route(info['module']), methods=['GET', 'POST'])

# -----------------------------------------
# Main entry
# -----------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)