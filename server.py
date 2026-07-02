from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='.')
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('cases.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT UNIQUE,
        title TEXT,
        dispute_type TEXT,
        latitude REAL,
        longitude REAL,
        parties TEXT,
        description TEXT,
        reporter_name TEXT,
        contact TEXT,
        documents TEXT,
        status TEXT DEFAULT 'Pending',
        mediator TEXT DEFAULT 'Unassigned',
        submitted_date TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/cases', methods=['POST'])
def submit_case():
    try:
        case_number = f"LD-{1000 + int(datetime.now().timestamp()) % 9000}"
        
        title = request.form.get('title')
        dispute_type = request.form.get('disputeType')
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        parties = request.form.get('parties')
        description = request.form.get('description')
        reporter_name = request.form.get('reporterName')
        contact = request.form.get('contact')
        
        uploaded_files = []
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"{case_number}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    uploaded_files.append(filename)
        
        conn = sqlite3.connect('cases.db')
        c = conn.cursor()
        c.execute('''INSERT INTO cases 
            (case_id, title, dispute_type, latitude, longitude, parties, 
             description, reporter_name, contact, documents, submitted_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (case_number, title, dispute_type, latitude, longitude, parties,
             description, reporter_name, contact, ','.join(uploaded_files),
             datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'caseId': case_number, 'files': uploaded_files})
    except Exception as e:
        print(f"❌ SERVER ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cases', methods=['GET'])
def get_cases():
    conn = sqlite3.connect('cases.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM cases ORDER BY id DESC')
    cases = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(cases)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect('cases.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM cases')
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM cases WHERE status='Pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM cases WHERE status='In Progress'")
    in_progress = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM cases WHERE status='Resolved'")
    resolved = c.fetchone()[0]
    conn.close()
    
    return jsonify({
        'total': total, 'pending': pending,
        'inProgress': in_progress, 'resolved': resolved
    })

if __name__ == '__main__':
    print(" Server running at http://127.0.0.1:5000")
    print("📱 For mobile access, use your computer's IP address")
    app.run(debug=True, host='0.0.0.0', port=5000)