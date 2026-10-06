import os
from flask import Flask, render_template, redirect, url_for, Blueprint, send_from_directory
from models import db, ensure_db_schema
from routes.auth_routes import auth_bp

app = Flask(__name__)

# Base Directory & Configurations
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'edusync.db')
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
os.makedirs(os.path.join(basedir, 'static', 'uploads'), exist_ok=True)

from datetime import timedelta

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SECRET_KEY'] = 'edusync_secure_key_2026'
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
def dashboard():
    return redirect(url_for('auth.tutor_dashboard'))

@student_bp.route('/dashboard')
def dashboard():
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
    return send_from_directory(os.path.join(basedir, 'static', 'uploads'), filename)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Ensure schema and columns exist
ensure_db_schema(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)