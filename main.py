import pyperclip
import socket
import os
import sys
import zipfile
import atexit
import shutil
from io import BytesIO
from flask import Flask, render_template_string, request, Response, send_from_directory, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

# 1. --- Configuration ---
PORT = 5000

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(application_path, 'uploads')


# 2. --- Flask App Initialization ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def cleanup_uploads():
    print("\n--- Shutting down and cleaning up uploaded files ---")
    try:
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
            print(f"Successfully removed '{UPLOAD_FOLDER}' directory.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

# Register the cleanup function to run when the app exits
atexit.register(cleanup_uploads)


# 3. --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Sharer</title>
    <style>
        :root { color-scheme: light dark; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            margin: 2em; 
            background-color: light-dark(#f4f4f9, #121212); 
            color: light-dark(#333, #e0e0e0);
            transition: background-color 0.3s, color 0.3s;
        }
        .container { 
            max-width: 800px; margin: auto; background-color: light-dark(#ffffff, #1e1e1e); 
            padding: 2em; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
        }
        h1, h2 { text-align: center; color: light-dark(#555, #cccccc); }
        textarea { 
            width: 95%; padding: 10px; margin-top: 10px; border-radius: 4px; 
            font-size: 1rem; resize: vertical; background-color: light-dark(#ffffff, #333333);
            color: light-dark(#000000, #ffffff); border: 1px solid light-dark(#ccc, #555);
        }
        .clipboard-content { background-color: light-dark(#eee, #2a2a2a); min-height: 100px; }
        .button-container { text-align: center; margin-top: 10px; }
        button, input[type=submit] { 
            background-color: #007bff; color: white; border: none; padding: 12px 20px; 
            border-radius: 4px; font-size: 1rem; cursor: pointer; transition: background-color 0.2s; 
        }
        button:hover, input[type=submit]:hover { background-color: #0056b3; }
        .copy-button { background-color: #6c757d; margin-top: 10px; }
        .copy-button:hover { background-color: #5a6268; }
        hr { border: none; height: 1px; margin: 2em 0; background-color: light-dark(#ddd, #444); }
        .file-list { list-style-type: none; padding: 0; }
        .file-list li { 
            background-color: light-dark(#f9f9f9, #2c2c2c); margin: 8px 0; padding: 10px 15px; 
            border-radius: 4px; display: flex; justify-content: space-between; align-items: center;
            gap: 15px;
        }
        .file-list li span {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            min-width: 0;
        }
        .file-list a {
            flex-shrink: 0;
        }
        .file-list a button { padding: 8px 12px; font-size: 0.9rem; }
        .download-all-btn { background-color: #28a745; margin-top: 15px; }
        .download-all-btn:hover { background-color: #218838; }
        .tab-container {
            overflow: hidden;
            border-bottom: 1px solid light-dark(#ccc, #444);
            margin-bottom: 20px;
        }
        .tab-link {
            background-color: transparent;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 1rem;
            color: inherit;
            border-bottom: 3px solid transparent;
        }
        .tab-link:hover {
            background-color: light-dark(#f1f1f1, #333);
        }
        .tab-link.active {
            border-bottom: 3px solid #007bff;
        }
        .tab-content {
            display: none;
            animation: fadeEffect 0.5s;
        }
        @keyframes fadeEffect {
            from {opacity: 0;}
            to {opacity: 1;}
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Local Sharer</h1>
        <div class="tab-container">
            <button class="tab-link {% if active_tab == 'Clipboard' %}active{% endif %}" onclick="openTab(event, 'Clipboard')">Clipboard</button>
            <button class="tab-link {% if active_tab == 'Files' %}active{% endif %}" onclick="openTab(event, 'Files')">Files</button>
        </div>

        <div id="Clipboard" class="tab-content" {% if active_tab == 'Clipboard' %}style="display: block;"{% endif %}>
            <h2>Clipboard Sharer</h2>
            <textarea id="clipboardDisplay" class="clipboard-content" readonly>{{ clipboard_text }}</textarea>
            <div class="button-container">
                 <button type="button" class="copy-button" onclick="copyToClipboard()">Copy Text</button>
            </div>
            <hr>
            <h2>Send to Clipboard</h2>
            <form id="sendForm">
                <textarea id="textToSend" name="text_to_send" rows="5" placeholder="Type or paste text here..."></textarea>
                <div class="button-container" style="margin-top:20px;">
                    <button type="submit">Send Text</button>
                </div>
            </form>
        </div>
        
        <div id="Files" class="tab-content" {% if active_tab == 'Files' %}style="display: block;"{% endif %}>
            <h2>File Sharer</h2>
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="files" multiple style="width: 100%; margin: 15px 0;">
                <div class="button-container">
                    <input type="submit" value="Upload Files">
                </div>
            </form>

            <h3 style="margin-top: 30px;">Shared Files</h3>
            <ul id="fileList" class="file-list">
            {% for file in files %}
                <li>
                    <span>{{ file.name }}</span>
                    <a href="{{ file.url }}"><button>Download</button></a>
                </li>
            {% endfor %}
            </ul>
            <div id="downloadAllContainer" class="button-container" {% if not files %}style="display: none;"{% endif %}>
                <a href="{{ url_for('download_all') }}"><button class="download-all-btn">Download All as ZIP</button></a>
            </div>
            <p id="noFilesMessage" style="text-align:center; {% if files %}display: none;{% endif %}">No files have been shared yet.</p>
        </div>
    </div>
    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tab-link");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }

        function copyToClipboard() {
            const textarea = document.getElementById('clipboardDisplay');
            const copyButton = document.querySelector('.copy-button');
            textarea.select();
            textarea.setSelectionRange(0, 99999); 
            try {
                const successful = document.execCommand('copy');
                copyButton.textContent = successful ? 'Copied!' : 'Failed!';
            } catch (err) {
                copyButton.textContent = 'Error!';
                console.error('An error occurred during copy:', err);
            }
            setTimeout(() => { copyButton.textContent = 'Copy Text'; }, 2000);
            window.getSelection().removeAllRanges();
        }

        document.getElementById('sendForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const textToSendArea = document.getElementById('textToSend');
            const text = textToSendArea.value;
            if (text) {
                await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `text_to_send=${encodeURIComponent(text)}`
                });
                textToSendArea.value = '';
            }
        });

        const clipboardTextarea = document.getElementById('clipboardDisplay');
        setInterval(async () => {
            try {
                const response = await fetch('/get-clipboard-data');
                const newText = await response.text();
                if (clipboardTextarea.value !== newText) {
                    clipboardTextarea.value = newText;
                }
            } catch (error) {
                console.error("Failed to fetch clipboard data:", error);
            }
        }, 2000);

        const fileListUl = document.getElementById('fileList');
        const noFilesMessage = document.getElementById('noFilesMessage');
        const downloadAllContainer = document.getElementById('downloadAllContainer');
        let currentFilesJson = JSON.stringify({{ files|tojson }});

        setInterval(async () => {
            try {
                const response = await fetch('/get-file-list');
                const newFiles = await response.json();
                const newFilesJson = JSON.stringify(newFiles);

                if (currentFilesJson !== newFilesJson) {
                    currentFilesJson = newFilesJson;
                    updateFileListDOM(newFiles);
                }
            } catch (error) {
                console.error("Failed to fetch file list:", error);
            }
        }, 2000);

        function updateFileListDOM(files) {
            fileListUl.innerHTML = ''; 

            if (files.length === 0) {
                noFilesMessage.style.display = 'block';
                downloadAllContainer.style.display = 'none';
            } else {
                noFilesMessage.style.display = 'none';
                downloadAllContainer.style.display = 'block';
                
                files.forEach(file => {
                    const li = document.createElement('li');
                    const span = document.createElement('span');
                    span.textContent = file.name;
                    
                    const a = document.createElement('a');
                    a.href = file.url;
                    
                    const button = document.createElement('button');
                    button.textContent = 'Download';
                    
                    a.appendChild(button);
                    li.appendChild(span);
                    li.appendChild(a);
                    
                    fileListUl.appendChild(li);
                });
            }
        }
    </script>
</body>
</html>
"""

# 4. --- Application Logic ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'files' in request.files and request.files.getlist('files')[0].filename:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('index', active_tab='Files'))

        text_from_device = request.form.get('text_to_send')
        if text_from_device is not None:
            pyperclip.copy(text_from_device)
            return ('', 204)
    
    active_tab = request.args.get('active_tab', 'Clipboard')
    clipboard_content = pyperclip.paste()
    
    upload_folder = app.config['UPLOAD_FOLDER']
    try:
        filenames = sorted(
            os.listdir(upload_folder),
            key=lambda f: os.path.getmtime(os.path.join(upload_folder, f)),
            reverse=True
        )
        files_for_template = [{'name': f, 'url': url_for('uploaded_file', filename=f)} for f in filenames]
    except FileNotFoundError:
        files_for_template = []

    return render_template_string(HTML_TEMPLATE, clipboard_text=clipboard_content, files=files_for_template, active_tab=active_tab)

@app.route('/get-clipboard-data')
def get_clipboard_data():
    content = pyperclip.paste()
    return Response(content, mimetype='text/plain')

@app.route('/get-file-list')
def get_file_list():
    upload_folder = app.config['UPLOAD_FOLDER']
    try:
        filenames = sorted(
            os.listdir(upload_folder),
            key=lambda f: os.path.getmtime(os.path.join(upload_folder, f)),
            reverse=True
        )
        files_with_urls = [{'name': f, 'url': url_for('uploaded_file', filename=f)} for f in filenames]
    except FileNotFoundError:
        files_with_urls = []
    return jsonify(files_with_urls)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/download-all')
def download_all():
    memory_file = BytesIO()
    upload_folder = app.config['UPLOAD_FOLDER']
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            zf.write(file_path, arcname=filename)
    memory_file.seek(0)
    
    return Response(
        memory_file,
        mimetype='application/zip',
        headers={'Content-Disposition': 'attachment;filename=shared_files.zip'}
    )

# 5. --- Server Startup ---
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1' 
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    host_ip = get_local_ip()
    print("--- Local Sharer ---")
    print(f"Server is running. Open your browser and go to:")
    print(f"http://{host_ip}:{PORT}")
    print("---------------------------------")
    print("Press CTRL+C to stop the server.")
    app.run(host=host_ip, port=PORT, debug=False)

