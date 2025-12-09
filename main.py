import pyperclip
import socket
import os
import sys
import zipfile
import atexit
import shutil
import threading
import time
from io import BytesIO
from flask import Flask, render_template, request, Response, send_from_directory, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename

# --- Configuration ---
class Config:
    PORT = 5000
    # 16GB Upload Limit
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 * 1024  
    # SECURITY PIN: Leave empty "" for no password, or set a code like "1234"
    APP_PIN = "361022" 
    SECRET_KEY = 'super-secret-key-for-sessions' # Required for login sessions

    @staticmethod
    def get_base_path():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

# --- Server Class ---
class LocalShareServer:
    def __init__(self):
        self.base_path = Config.get_base_path()
        self.upload_folder = os.path.join(self.base_path, 'uploads')
        
        self.app = Flask(__name__, 
                         template_folder=os.path.join(self.base_path, 'templates'),
                         static_folder=os.path.join(self.base_path, 'static'))
        
        self.configure_app()
        self.register_routes()
        self.setup_cleanup()

    def configure_app(self):
        self.app.config['UPLOAD_FOLDER'] = self.upload_folder
        self.app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
        self.app.config['SECRET_KEY'] = Config.SECRET_KEY

        if os.path.exists(self.upload_folder):
            try:
                shutil.rmtree(self.upload_folder)
                print(">> PREVIOUS SESSION FILES CLEARED.")
            except Exception as e:
                print(f">> ERROR CLEARING CACHE: {e}")

        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

    def setup_cleanup(self):
        def cleanup():
            if os.path.exists(self.upload_folder):
                try:
                    shutil.rmtree(self.upload_folder)
                except:
                    pass
        atexit.register(cleanup)

    def register_routes(self):
        self.app.add_url_rule('/', view_func=self.index, methods=['GET', 'POST'])
        self.app.add_url_rule('/login', view_func=self.login, methods=['POST'])
        self.app.add_url_rule('/logout', view_func=self.logout)
        self.app.add_url_rule('/shutdown', view_func=self.shutdown, methods=['POST'])
        
        self.app.add_url_rule('/api/clipboard', view_func=self.api_clipboard)
        self.app.add_url_rule('/api/files', view_func=self.api_files)
        
        self.app.add_url_rule('/uploads/<filename>', view_func=self.download_file)
        self.app.add_url_rule('/download-zip', view_func=self.download_zip)

    # --- Auth Helper ---
    def is_authenticated(self):
        if not Config.APP_PIN: return True # No PIN set = always allowed
        return session.get('authenticated') == True

    # --- Routes ---
    def index(self):
        if not self.is_authenticated():
            return render_template('login.html') # Serve Login Page

        active_tab = request.args.get('tab', 'clipboard')
        
        if request.method == 'POST':
            # File Upload
            if 'files' in request.files:
                files = request.files.getlist('files')
                if files and files[0].filename:
                    for file in files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            # Save directly to disk to avoid RAM lag on phones
                            file.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                    return redirect(url_for('index', tab='files'))
            
            # Send Text
            text_sent = request.form.get('text_to_send')
            if text_sent:
                try: pyperclip.copy(text_sent)
                except: pass
                return ('', 204)

        try: clipboard_text = pyperclip.paste()
        except: clipboard_text = ""
        return render_template('index.html', clipboard_text=clipboard_text, active_tab=active_tab)

    def login(self):
        pin = request.form.get('pin')
        if pin == Config.APP_PIN:
            session['authenticated'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error="INVALID PIN")

    def logout(self):
        session.clear()
        return redirect(url_for('index'))

    def shutdown(self):
        if not self.is_authenticated(): return "Unauthorized", 401
        
        # Helper to kill server in a separate thread so the request can finish returning "OK"
        def kill_server():
            time.sleep(1)
            print(">> SHUTTING DOWN...")
            os._exit(0)
            
        threading.Thread(target=kill_server).start()
        return jsonify({"status": "Server shutting down..."})

    # --- APIs (Lag Reduction: Only send JSON) ---
    def api_clipboard(self):
        if not self.is_authenticated(): return "", 401
        try: return Response(pyperclip.paste(), mimetype='text/plain')
        except: return Response("", mimetype='text/plain')

    def api_files(self):
        if not self.is_authenticated(): return jsonify([])
        try:
            files = sorted(os.listdir(self.upload_folder), key=lambda f: os.path.getmtime(os.path.join(self.upload_folder, f)), reverse=True)
            data = [{'name': f, 'url': url_for('download_file', filename=f)} for f in files]
        except: data = []
        return jsonify(data)

    def download_file(self, filename):
        if not self.is_authenticated(): return "Unauthorized", 401
        return send_from_directory(self.app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

    def download_zip(self):
        if not self.is_authenticated(): return "Unauthorized", 401
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in os.listdir(self.upload_folder):
                zf.write(os.path.join(self.upload_folder, filename), arcname=filename)
        memory_file.seek(0)
        return Response(memory_file, mimetype='application/zip', headers={'Content-Disposition': 'attachment;filename=shared.zip'})

    def run(self):
        host_ip = self._get_ip()
        print(f"\n--- LOCAL SHARE ONLINE ---")
        print(f"Address: http://{host_ip}:{Config.PORT}")
        print(f"PIN Code: {Config.APP_PIN if Config.APP_PIN else 'None'}")
        # threaded=True prevents lag during multiple uploads
        self.app.run(host='0.0.0.0', port=Config.PORT, debug=False, threaded=True)

    def _get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
        except: return '127.0.0.1'
        finally: s.close()

if __name__ == '__main__':
    LocalShareServer().run()
