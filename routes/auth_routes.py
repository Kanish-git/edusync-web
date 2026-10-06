import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from sqlalchemy import func
from models import db, User, Assignment, Submission, Notice

# Blueprint must be defined at the top
auth_bp = Blueprint('auth', __name__)

# Setup for document uploads with serverless / read-only fallback
def get_upload_folder():
    """Retrieve the configured upload folder, falling back to /tmp/uploads if read-only."""
    try:
        from flask import current_app
        folder = current_app.config.get('UPLOAD_FOLDER')
        if folder:
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass
            return folder
    except Exception:
        pass
    
    # Check if static/uploads is writable
    static_uploads = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    try:
        os.makedirs(static_uploads, exist_ok=True)
        return static_uploads
    except Exception:
        # Fallback to serverless /tmp
        tmp_uploads = '/tmp/uploads'
        try:
            os.makedirs(tmp_uploads, exist_ok=True)
        except Exception:
            pass
        return tmp_uploads

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    UPLOAD_FOLDER = '/tmp/uploads'
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    except Exception:
        pass


# ==========================================
# TUTOR PORTAL ROUTES
# ==========================================

@auth_bp.route('/register_tutor', methods=['GET', 'POST'])
@auth_bp.route('/register-tutor', methods=['GET', 'POST'])
def register_tutor():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Username and password are required!', 'danger')
            return render_template('register_tutor.html')
        
        existing = User.query.filter(func.lower(User.username) == username.lower()).first()
        if existing:
            flash('Username already exists! Please choose another.', 'warning')
            return render_template('register_tutor.html')
        
        new_tutor = User(username=username, password=password, role='Tutor', is_verified=True, is_banned=False)
        db.session.add(new_tutor)
        db.session.commit()
        flash('Tutor account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login_tutor'))
    return render_template('register_tutor.html')


@auth_bp.route('/login_tutor', methods=['GET', 'POST'])
@auth_bp.route('/tutor-login', methods=['GET', 'POST'])
@auth_bp.route('/tutor-login-submit', methods=['GET', 'POST'])
@auth_bp.route('/tutor_login', methods=['GET', 'POST'])
def login_tutor():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login_tutor.html')

        # Check database for registered tutor (case-insensitive username)
        user = User.query.filter(
            func.lower(User.username) == username.lower(), 
            func.lower(User.role) == 'tutor'
        ).first()

        if user and user.password == password:
            session.permanent = True
            session['role'] = 'tutor'
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('auth.tutor_dashboard'))

        # Fallback for default admin
        if username.lower() == 'admin' and password in ('admin', 'admin123'):
            session.permanent = True
            session['role'] = 'tutor'
            session['user_id'] = 1
            session['username'] = 'admin'
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('auth.tutor_dashboard'))

        flash('Invalid tutor username or password. Please try again.', 'danger')
        return render_template('login_tutor.html', error='Invalid Tutor Login')
    return render_template('login_tutor.html')


@auth_bp.route('/tutor_dashboard', methods=['GET', 'POST'])
@auth_bp.route('/tutor-dashboard', methods=['GET', 'POST'])
def tutor_dashboard():
    if session.get('role') != 'tutor':
        flash('Please log in as a tutor first.', 'warning')
        return redirect(url_for('auth.login_tutor'))

    if request.method == 'POST':
        topic = request.form.get('topic_name', '').strip()
        desc = request.form.get('task_description', '').strip()
        deadline = request.form.get('deadline', '').strip()
        category = request.form.get('category', 'Computer Science').strip()
        difficulty = request.form.get('difficulty', 'Intermediate').strip()
        priority = request.form.get('priority', 'Standard').strip()
        
        try:
            max_marks = int(request.form.get('max_marks', 100))
        except (ValueError, TypeError):
            max_marks = 100

        file = request.files.get('document')
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            try:
                dest_dir = get_upload_folder()
                file.save(os.path.join(dest_dir, filename))
            except Exception as up_err:
                print("[EduSync] Assignment upload save note:", up_err)

        if topic and desc:
            new_assignment = Assignment(
                topic_name=topic, 
                task_description=desc, 
                document_path=filename,
                deadline=deadline,
                category=category,
                difficulty=difficulty,
                max_marks=max_marks,
                priority=priority
            )
            db.session.add(new_assignment)
            db.session.commit()
            flash(f'Assignment "{topic}" published to class successfully!', 'success')

    students = User.query.filter(func.lower(User.role) == 'student').order_by(User.id.desc()).all()
    raw_submissions = Submission.query.order_by(Submission.timestamp.desc()).all()
    results = list(raw_submissions)

    # For the latest assignment, include pending entries for students who have not yet submitted
    latest_assignment = Assignment.query.order_by(Assignment.id.desc()).first()
    if latest_assignment:
        submitted_regs = {s.register_number.upper() for s in raw_submissions if s.topic_name == latest_assignment.topic_name}
        for st in students:
            if st.register_number and st.register_number.upper() not in submitted_regs:
                results.append(type('PendingResult', (), {
                    'id': f'p-{st.id}',
                    'student_name': st.username,
                    'register_number': st.register_number,
                    'topic_name': latest_assignment.topic_name,
                    'status': 'pending',
                    'score': None,
                    'feedback': None,
                    'submission_text': None,
                    'submission_file': None,
                    'student_notes': None
                })())

    # Build assignment history
    all_assignments = Assignment.query.order_by(Assignment.id.desc()).all()
    history = []
    all_topics = []
    for a in all_assignments:
        all_topics.append(a.topic_name)
        sub_count = Submission.query.filter_by(topic_name=a.topic_name).count()
        history.append({
            'id': a.id,
            'topic_name': a.topic_name,
            'task_description': a.task_description,
            'posted_at': a.date_uploaded.strftime('%Y-%m-%d %H:%M') if a.date_uploaded else 'Recently',
            'submission_count': sub_count,
            'document_path': a.document_path,
            'deadline': a.deadline,
            'category': a.category or 'Computer Science',
            'difficulty': a.difficulty or 'Intermediate',
            'max_marks': a.max_marks or 100,
            'priority': a.priority or 'Standard'
        })

    active_notice = Notice.query.order_by(Notice.id.desc()).first()

    return render_template(
        'tutor_dashboard.html', 
        students=students, 
        results=results, 
        history=history, 
        all_topics=all_topics,
        active_notice=active_notice
    )


@auth_bp.route('/post-announcement', methods=['POST'])
def post_announcement():
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    message = request.form.get('message', '').strip()
    level = request.form.get('level', 'info').strip()
    if not message:
        flash('Announcement text cannot be empty.', 'warning')
        return redirect(url_for('auth.tutor_dashboard'))
    
    notice = Notice(message=message, level=level, posted_by=session.get('username', 'Tutor'))
    db.session.add(notice)
    db.session.commit()
    flash('Class announcement broadcasted to all students.', 'success')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/delete-announcement/<int:notice_id>', methods=['POST'])
def delete_announcement(notice_id):
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    flash('Announcement dismissed.', 'info')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/delete-assignment/<int:assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    assign = Assignment.query.get_or_404(assignment_id)
    try:
        Submission.query.filter_by(topic_name=assign.topic_name).delete()
        if assign.document_path:
            file_path = os.path.join(UPLOAD_FOLDER, assign.document_path)
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except Exception: pass
        db.session.delete(assign)
        db.session.commit()
        flash(f'Assignment "{assign.topic_name}" and its submissions deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting assignment: {str(e)}', 'danger')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/update-submission-status/<int:sub_id>', methods=['POST'])
def update_submission_status(sub_id):
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    new_status = request.form.get('status', 'Cleared').strip()
    sub = Submission.query.get_or_404(sub_id)
    sub.status = new_status
    db.session.commit()
    flash(f'Submission for {sub.student_name} marked as {new_status}.', 'success')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/grade-submission/<int:sub_id>', methods=['POST'])
def grade_submission(sub_id):
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    status = request.form.get('status', 'Cleared').strip()
    score = request.form.get('score', '').strip()
    feedback = request.form.get('feedback', '').strip()

    sub = Submission.query.get_or_404(sub_id)
    sub.status = status
    if score:
        sub.score = score
    if feedback:
        sub.feedback = feedback
    db.session.commit()
    flash(f'Graded submission for {sub.student_name} ({status}, Score: {score or "Recorded"}).', 'success')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/batch-submissions-action', methods=['POST'])
def batch_submissions_action():
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    action = request.form.get('action', '').strip()
    raw_ids = request.form.get('selected_ids', '').strip()
    if not raw_ids:
        flash('No submissions were selected.', 'warning')
        return redirect(url_for('auth.tutor_dashboard'))

    id_list = []
    for x in raw_ids.split(','):
        x = x.strip()
        if x.isdigit():
            id_list.append(int(x))

    if not id_list:
        flash('No valid submissions selected.', 'warning')
        return redirect(url_for('auth.tutor_dashboard'))

    try:
        if action == 'mark_cleared':
            Submission.query.filter(Submission.id.in_(id_list)).update({Submission.status: 'Cleared'}, synchronize_session=False)
            flash(f'Batch updated: {len(id_list)} submissions marked as Cleared.', 'success')
        elif action == 'mark_pending':
            Submission.query.filter(Submission.id.in_(id_list)).update({Submission.status: 'pending'}, synchronize_session=False)
            flash(f'Batch updated: {len(id_list)} submissions marked as Pending.', 'warning')
        elif action == 'mark_failed':
            Submission.query.filter(Submission.id.in_(id_list)).update({Submission.status: 'failed'}, synchronize_session=False)
            flash(f'Batch updated: {len(id_list)} submissions marked as Failed.', 'danger')
        elif action == 'delete':
            Submission.query.filter(Submission.id.in_(id_list)).delete(synchronize_session=False)
            flash(f'Batch deleted: {len(id_list)} submissions removed.', 'info')
        else:
            flash('Unknown batch action.', 'warning')
            return redirect(url_for('auth.tutor_dashboard'))
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Batch operation failed: {str(e)}', 'danger')

    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/toggle-student-verification/<int:student_id>', methods=['POST'])
def toggle_student_verification(student_id):
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    st = User.query.get_or_404(student_id)
    st.is_verified = not bool(st.is_verified)
    db.session.commit()
    state = "verified" if st.is_verified else "unverified"
    flash(f'Student {st.username} is now {state}.', 'info')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/batch-verify-students', methods=['POST'])
def batch_verify_students():
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    User.query.filter(func.lower(User.role) == 'student').update({User.is_verified: True}, synchronize_session=False)
    db.session.commit()
    flash('All enrolled students have been verified successfully.', 'success')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/enroll-student-direct', methods=['POST'])
def enroll_student_direct():
    if session.get('role') != 'tutor':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('auth.login_tutor'))
    username = request.form.get('student_name', '').strip()
    reg_no = request.form.get('register_number', '').strip()
    if not username or not reg_no:
        flash('Student name and register number are required.', 'warning')
        return redirect(url_for('auth.tutor_dashboard'))
    existing = User.query.filter(
        (func.lower(User.username) == username.lower()) | 
        (func.lower(User.register_number) == reg_no.lower())
    ).first()
    if existing:
        flash('A student with this name or register number is already enrolled.', 'warning')
        return redirect(url_for('auth.tutor_dashboard'))
    new_student = User(username=username, register_number=reg_no, role='Student', is_verified=True, is_banned=False)
    db.session.add(new_student)
    db.session.commit()
    flash(f'Student "{username}" ({reg_no}) enrolled successfully.', 'success')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/delete_student/<int:student_id>', methods=['POST'])
@auth_bp.route('/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'Student':
        flash('Invalid action!', 'danger')
        return redirect(url_for('auth.tutor_dashboard'))
    try:
        if student.register_number:
            Submission.query.filter_by(register_number=student.register_number).delete(synchronize_session=False)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student "{student.username}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'danger')
    return redirect(url_for('auth.tutor_dashboard'))


@auth_bp.route('/delete_student_by_name', methods=['POST'])
@auth_bp.route('/delete-student-by-name', methods=['POST'])
def delete_student_by_name():
    student_name = request.form.get('student_name', '').strip()
    reg_no = request.form.get('register_number', '').strip()
    student = None
    if reg_no and reg_no != 'N/A':
        student = User.query.filter(func.lower(User.register_number) == reg_no.lower(), func.lower(User.role) == 'student').first()
    if not student and student_name:
        student = User.query.filter(func.lower(User.username) == student_name.lower(), func.lower(User.role) == 'student').first()
    if not student:
        flash(f'Student record not found.', 'warning')
        return redirect(url_for('auth.tutor_dashboard'))
    try:
        if student.register_number:
            Submission.query.filter_by(register_number=student.register_number).delete(synchronize_session=False)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student "{student.username}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('auth.tutor_dashboard'))


# ==========================================
# STUDENT PORTAL ROUTES
# ==========================================

@auth_bp.route('/register_student', methods=['GET', 'POST'])
@auth_bp.route('/register-student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        username = (request.form.get('student_name') or request.form.get('username') or '').strip()
        reg_no = request.form.get('register_number', '').strip()
        
        if not username or not reg_no:
            flash('Student Name and Register Number are required!', 'danger')
            return render_template('register_student.html')

        existing_reg = User.query.filter(func.lower(User.register_number) == reg_no.lower()).first()
        if existing_reg:
            flash('This Register Number is already registered! Please log in.', 'warning')
            return redirect(url_for('auth.login_student'))

        existing_user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if existing_user:
            flash('This Student Name is already registered! Please choose a distinct name.', 'warning')
            return render_template('register_student.html')

        new_student = User(
            username=username,
            register_number=reg_no,
            role='Student',
            is_verified=True,
            is_banned=False
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful! Please log in with your name or register number.', 'success')
        return redirect(url_for('auth.login_student'))

    return render_template('register_student.html')


@auth_bp.route('/login_student', methods=['GET', 'POST'])
@auth_bp.route('/student-login', methods=['GET', 'POST'])
@auth_bp.route('/student-login-submit', methods=['GET', 'POST'])
@auth_bp.route('/student_login', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        student_name = (request.form.get('student_name') or request.form.get('username') or '').strip()
        reg_no = request.form.get('register_number', '').strip()

        if not reg_no and not student_name:
            flash('Please provide your student name or register number.', 'warning')
            return render_template('login_student.html')

        student = None
        # 1. Match by Register Number (case-insensitive)
        if reg_no:
            student = User.query.filter(
                func.lower(User.register_number) == reg_no.lower(),
                func.lower(User.role) == 'student'
            ).first()

        # 2. If not found by reg_no, match by Student Name (case-insensitive)
        if not student and student_name:
            student = User.query.filter(
                func.lower(User.username) == student_name.lower(),
                func.lower(User.role) == 'student'
            ).first()

        if student:
            if student.is_banned:
                flash('This student account is suspended. Contact your tutor.', 'danger')
                return render_template('login_student.html', error='Account Suspended')
            session.permanent = True
            session['role'] = 'student'
            session['user_id'] = student.id
            session['username'] = student.username
            session['register_number'] = student.register_number or reg_no
            flash(f'Welcome, {student.username}!', 'success')
            return redirect(url_for('auth.student_dashboard'))

        # Fallback for default demo student
        if (student_name and student_name.lower() in ('test student', 'student')) or (reg_no and reg_no.upper() == 'REG001'):
            session.permanent = True
            session['role'] = 'student'
            session['user_id'] = 4
            session['username'] = 'Test Student'
            session['register_number'] = 'REG001'
            flash('Welcome, Test Student!', 'success')
            return redirect(url_for('auth.student_dashboard'))

        flash('Invalid Student Login! Please verify your name and register number.', 'danger')
        return render_template('login_student.html', error='Invalid Student Login')
    return render_template('login_student.html')


@auth_bp.route('/student_dashboard')
@auth_bp.route('/student-dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        flash('Please log in as a student first.', 'warning')
        return redirect(url_for('auth.login_student'))

    reg_no = session.get('register_number') or ''
    student_name = session.get('username') or ''
    raw_assignments = Assignment.query.order_by(Assignment.id.desc()).all()
    assignments = []
    
    for a in raw_assignments:
        sub = None
        if reg_no:
            sub = Submission.query.filter(
                func.lower(Submission.register_number) == reg_no.lower(),
                Submission.topic_name == a.topic_name
            ).first()
        if not sub and student_name:
            sub = Submission.query.filter(
                func.lower(Submission.student_name) == student_name.lower(),
                Submission.topic_name == a.topic_name
            ).first()

        assignments.append({
            'id': a.id,
            'topic_name': a.topic_name,
            'task_description': a.task_description,
            'document_path': a.document_path,
            'deadline': a.deadline,
            'category': a.category or 'Computer Science',
            'difficulty': a.difficulty or 'Intermediate',
            'max_marks': a.max_marks or 100,
            'priority': a.priority or 'Standard',
            'completed': sub is not None and sub.status == 'Cleared',
            'status': sub.status if sub else 'Pending',
            'score': sub.score if sub else None,
            'feedback': sub.feedback if sub else None,
            'submission_text': sub.submission_text if sub else None,
            'submission_file': sub.submission_file if sub else None,
            'student_notes': sub.student_notes if sub else None
        })
    active_notice = Notice.query.order_by(Notice.id.desc()).first()
    return render_template('student_dashboard.html', assignments=assignments, active_notice=active_notice)


@auth_bp.route('/complete_task/<int:task_id>', methods=['POST'])
@auth_bp.route('/complete-task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    if session.get('role') != 'student':
        flash('Please log in as a student.', 'warning')
        return redirect(url_for('auth.login_student'))

    assignment = Assignment.query.get_or_404(task_id)
    student_name = session.get('username') or 'Student'
    reg_no = session.get('register_number') or 'N/A'

    solution_text = request.form.get('solution_text', '').strip()
    student_notes = request.form.get('student_notes', '').strip()
    file = request.files.get('solution_file')

    solution_filename = None
    if file and file.filename != '':
        solution_filename = secure_filename(f"{reg_no}_{assignment.id}_{file.filename}")
        try:
            dest_dir = get_upload_folder()
            file.save(os.path.join(dest_dir, solution_filename))
        except Exception as up_err:
            print("[EduSync] Student upload save note:", up_err)

    existing_sub = Submission.query.filter(
        func.lower(Submission.register_number) == reg_no.lower(),
        Submission.topic_name == assignment.topic_name
    ).first()

    if not existing_sub:
        new_sub = Submission(
            student_name=student_name,
            register_number=reg_no,
            topic_name=assignment.topic_name,
            status='Cleared',
            submission_text=solution_text if solution_text else None,
            submission_file=solution_filename if solution_filename else None,
            student_notes=student_notes if student_notes else None
        )
        db.session.add(new_sub)
        db.session.commit()
        flash(f'Assignment "{assignment.topic_name}" submitted successfully!', 'success')
    else:
        existing_sub.status = 'Cleared'
        if solution_text:
            existing_sub.submission_text = solution_text
        if solution_filename:
            existing_sub.submission_file = solution_filename
        if student_notes:
            existing_sub.student_notes = student_notes
        db.session.commit()
        flash(f'Submission for "{assignment.topic_name}" updated!', 'info')

    return redirect(url_for('auth.student_dashboard'))


# ==========================================
# LOGOUT
# ==========================================

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect('/')