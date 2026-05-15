import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from models import db, User, Assignment, Submission

# Blueprint must be defined at the top
auth_bp = Blueprint('auth', __name__)

# Setup for document uploads
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- TUTOR PORTAL ROUTES ---
@auth_bp.route('/register_tutor', methods=['GET', 'POST'])
def register_tutor():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('auth.register_tutor'))
        new_tutor = User(username=username, password=password, role='Tutor')
        db.session.add(new_tutor)
        db.session.commit()
        return redirect(url_for('auth.login_tutor'))
    return render_template('register_tutor.html')

@auth_bp.route('/login_tutor', methods=['GET', 'POST'])
def login_tutor():
    if request.method == 'POST':
        return redirect(url_for('auth.tutor_dashboard'))
    return render_template('login_tutor.html')

@auth_bp.route('/tutor_dashboard', methods=['GET', 'POST'])
def tutor_dashboard():
    if request.method == 'POST':
        topic = request.form.get('topic_name')
        desc = request.form.get('task_description')
        file = request.files.get('document')
        
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        new_assignment = Assignment(topic_name=topic, task_description=desc, document_path=filename)
        db.session.add(new_assignment)
        db.session.commit()
        flash('Topic and document posted successfully!')

    students = User.query.filter_by(role='Student').order_by(User.id.desc()).all()
    results = Submission.query.order_by(Submission.timestamp.desc()).all()
    return render_template('tutor_dashboard.html', students=students, results=results)

@auth_bp.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'Student':
        flash('Invalid action!')
        return redirect(url_for('auth.tutor_dashboard'))
    try:
        Submission.query.filter_by(register_number=student.register_number).delete(synchronize_session=False)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student "{student.username}" deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}')
    return redirect(url_for('auth.tutor_dashboard'))

@auth_bp.route('/delete_student_by_name', methods=['POST'])
def delete_student_by_name():
    student_name = request.form.get('student_name', '').strip()
    reg_no = request.form.get('register_number', '').strip()
    # Try to find by register number, then by name
    student = None
    if reg_no and reg_no != 'N/A':
        student = User.query.filter_by(register_number=reg_no, role='Student').first()
    if not student and student_name:
        student = User.query.filter_by(username=student_name, role='Student').first()
    if not student:
        flash(f'Student not found! (name={student_name}, reg={reg_no})')
        return redirect(url_for('auth.tutor_dashboard'))
    try:
        Submission.query.filter_by(register_number=student.register_number).delete(synchronize_session=False)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student "{student.username}" deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}')
    return redirect(url_for('auth.tutor_dashboard'))

# --- STUDENT PORTAL ROUTES ---
@auth_bp.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        username = request.form.get('username')
        reg_no = request.form.get('register_number')
        if User.query.filter_by(username=username).first():
            flash('Name already registered!')
            return redirect(url_for('auth.register_student'))
        new_student = User(username=username, register_number=reg_no, role='Student')
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('auth.login_student'))
    return render_template('register_student.html')

@auth_bp.route('/login_student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        return redirect(url_for('auth.student_dashboard'))
    return render_template('login_student.html')

@auth_bp.route('/student_dashboard')
def student_dashboard():
    # Sending 'stats' variable to prevent UndefinedErrors in the template
    stats = {'total_available': 0, 'completed': 0, 'pending': 0}
    return render_template('student_dashboard.html', stats=stats)