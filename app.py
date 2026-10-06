import os
import shutil
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, Blueprint, send_from_directory, jsonify
from models import db, ensure_db_schema
from routes.auth_routes import auth_bp

# Base Directory & Environment Detection
basedir = os.path.abspath(os.path.dirname(__file__))
is_serverless = bool(
    os.environ.get('VERCEL') or 
    os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or 
    os.environ.get('LAMBDA_TASK_ROOT')
)

# Configure Instance & Upload Folders (with serverless /tmp protection)
if is_serverless:
    instance_path = '/tmp/instance'
    upload_folder = '/tmp/uploads'
    db_path = '/tmp/edusync.db'

    try:
        os.makedirs(instance_path, exist_ok=True)
    except Exception:
        pass

    try:
        os.makedirs(upload_folder, exist_ok=True)
    except Exception:
        pass

    # Copy bundled seed SQLite database to /tmp if present and not yet initialized
    try:
        bundled_dbs = [
            os.path.join(basedir, 'instance', 'edusync.db'),
            os.path.join(basedir, 'edusync.db'),
            os.path.join(basedir, 'database.db')
        ]
        if not os.path.exists(db_path):
            for candidate in bundled_dbs:
                if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
                    shutil.copyfile(candidate, db_path)
                    break
    except Exception as copy_err:
        print("[EduSync] Seed db copy note:", copy_err)

    app = Flask(__name__, instance_path=instance_path)
else:
    instance_path = os.path.join(basedir, 'instance')
    upload_folder = os.path.join(basedir, 'static', 'uploads')
    db_path = os.path.join(instance_path, 'edusync.db')

    try:
        os.makedirs(instance_path, exist_ok=True)
    except Exception:
        pass

    try:
        os.makedirs(upload_folder, exist_ok=True)
    except Exception:
        pass

    app = Flask(__name__)

# Database URI (supports remote PostgreSQL / Supabase / Neon or fallback SQLite)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"

app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'edusync_secure_key_2026')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Database
db.init_app(app)

# Register main Auth / Portal Blueprint
app.register_blueprint(auth_bp)

# Blueprint aliases for templates referencing tutor.dashboard and student.dashboard
tutor_bp = Blueprint('tutor', __name__)
student_bp = Blueprint('student', __name__)

@tutor_bp.route('/dashboard')
@tutor_bp.route('/manage_assignments')
@tutor_bp.route('/post_assignment')
@tutor_bp.route('/view_submissions')
@tutor_bp.route('/manage_students')
@tutor_bp.route('/performance_report')
def tutor_dashboard_alias():
    return redirect(url_for('auth.tutor_dashboard'))

@student_bp.route('/dashboard')
def student_dashboard_alias():
    return redirect(url_for('auth.student_dashboard'))

app.register_blueprint(tutor_bp, url_prefix='/tutor')
app.register_blueprint(student_bp, url_prefix='/student')

# Endpoint aliases for templates calling url_for('register_student'), url_for('student_login'), etc.
@app.route('/register-student-link', endpoint='register_student')
def register_student_link():
    return redirect(url_for('auth.register_student'))

@app.route('/student-login-link', endpoint='student_login')
def student_login_link():
    return redirect(url_for('auth.login_student'))

@app.route('/uploads/<path:filename>', endpoint='uploaded_file')
def uploaded_file(filename):
    current_upload = app.config.get('UPLOAD_FOLDER', os.path.join(basedir, 'static', 'uploads'))
    if os.path.exists(os.path.join(current_upload, filename)):
        return send_from_directory(current_upload, filename)
    fallback_upload = os.path.join(basedir, 'static', 'uploads')
    if os.path.exists(os.path.join(fallback_upload, filename)):
        return send_from_directory(fallback_upload, filename)
    return "File not found", 404

# Health check route for uptime monitoring / Vercel checks
@app.route('/health')
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "ok",
        "app": "EduSync",
        "serverless": is_serverless,
        "database": "configured"
    }), 200

# Favicon handler
@app.route('/favicon.ico')
def favicon():
    return ('', 204)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Ensure schema and initial accounts exist safely
try:
    ensure_db_schema(app)
except Exception as schema_err:
    print("[EduSync] DB schema startup note:", schema_err)

# WSGI Aliases for different serverless runners
application = app
handler = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)