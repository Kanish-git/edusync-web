import os
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
from database import get_db

tutor_bp = Blueprint('tutor', __name__)

def tutor_required(f):
    """Decorator to protect tutor routes."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'tutor':
            flash('Please log in as a tutor.', 'warning')
            return redirect(url_for('auth.login_tutor'))
        return f(*args, **kwargs)
    return decorated

@tutor_bp.route('/dashboard')
@tutor_required
def dashboard():
    from models import User, Assignment, Submission
    
    total_students = User.query.filter_by(role='Student').count()
    total_assignments = Assignment.query.count()
    total_submissions = Submission.query.count()

    stats = {
        'total_students': total_students,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions
    }
    return render_template('tutor/dashboard.html', stats=stats)

@tutor_bp.route('/post_assignment', methods=['GET', 'POST'])
@tutor_required
def post_assignment():
    if request.method == 'POST':
        from models import db, Assignment
        from datetime import date
        
        topic = request.form.get('topic')
        description = request.form.get('description')
        start_date = request.form.get('start_date') or date.today().isoformat()
        end_date = request.form.get('end_date') or date.today().isoformat()
        
        attachment_path = None
        file = request.files.get('attachment')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            attachment_path = filename
        
        new_assignment = Assignment(
            topic=topic, 
            description=description, 
            start_date=start_date, 
            end_date=end_date,
            attachment_path=attachment_path
        )
        db.session.add(new_assignment)
        db.session.commit()
        
        flash('Assignment posted successfully!', 'success')
        return redirect(url_for('tutor.dashboard'))
        
    return render_template('tutor/post_assignment.html')

@tutor_bp.route('/view_submissions')
@tutor_required
def view_submissions():
    from models import db, Submission, User, Assignment
    submissions = db.session.query(Submission, User, Assignment).\
        join(User, Submission.student_id == User.id).\
        join(Assignment, Submission.assignment_id == Assignment.id).\
        order_by(Submission.timestamp.desc()).all()
    
    return render_template('tutor/view_submissions.html', submissions=submissions)

@tutor_bp.route('/manage_assignments')
@tutor_required
def manage_assignments():
    from models import Assignment
    assignments = Assignment.query.order_by(Assignment.start_date.desc()).all()
    return render_template('tutor/manage_assignments.html', assignments=assignments)

@tutor_bp.route('/edit_assignment/<int:id>', methods=['GET', 'POST'])
@tutor_required
def edit_assignment(id):
    from models import db, Assignment
    assignment = Assignment.query.get_or_404(id)
    
    if request.method == 'POST':
        assignment.topic = request.form.get('topic')
        assignment.description = request.form.get('description')
        assignment.start_date = request.form.get('start_date')
        assignment.end_date = request.form.get('end_date')
        
        file = request.files.get('attachment')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            assignment.attachment_path = filename
            
        db.session.commit()
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('tutor.manage_assignments'))
        
    return render_template('tutor/edit_assignment.html', assignment=assignment)

@tutor_bp.route('/delete_assignment/<int:id>', methods=['POST'])
@tutor_required
def delete_assignment(id):
    from models import db, Assignment
    assignment = Assignment.query.get_or_404(id)
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted.', 'info')
    return redirect(url_for('tutor.manage_assignments'))

@tutor_bp.route('/toggle_assignment/<int:id>', methods=['POST'])
@tutor_required
def toggle_assignment(id):
    from models import db, Assignment
    assignment = Assignment.query.get_or_404(id)
    assignment.is_active = not assignment.is_active
    db.session.commit()
    status = "Active" if assignment.is_active else "Stopped"
    flash(f'Assignment status changed to {status}.', 'info')
    return redirect(url_for('tutor.manage_assignments'))

@tutor_bp.route('/performance_report')
@tutor_required
def performance_report():
    from models import User, Submission
    students = User.query.filter_by(role='Student').all()
    
    # Simple report: student name and their submission count
    report_data = []
    for student in students:
        sub_count = Submission.query.filter_by(student_id=student.id).count()
        report_data.append({
            'name': student.username,
            'reg_no': student.register_number,
            'submissions': sub_count
        })
        
    return render_template('tutor/performance_report.html', report_data=report_data)

@tutor_bp.route('/update_submission/<int:id>', methods=['POST'])
@tutor_required
def update_submission(id):
    from models import db, Submission
    submission = Submission.query.get_or_404(id)
    
    status = request.form.get('status')
    feedback = request.form.get('feedback')
    
    submission.status = status
    submission.feedback = feedback
    db.session.commit()
    
    flash('Submission evaluation updated!', 'success')
    return redirect(url_for('tutor.view_submissions'))
@tutor_bp.route('/manage_students')
@tutor_required
def manage_students():
    from models import User
    students = User.query.filter_by(role='Student').all()
    return render_template('tutor/manage_students.html', students=students)

@tutor_bp.route('/verify_student/<int:id>', methods=['POST'])
@tutor_required
def verify_student(id):
    from models import db, User
    student = User.query.get_or_404(id)
    student.is_verified = True
    db.session.commit()
    flash(f'Student {student.username} verified.', 'success')
    return redirect(url_for('tutor.manage_students'))

@tutor_bp.route('/ban_student/<int:id>', methods=['POST'])
@tutor_required
def ban_student(id):
    from models import db, User
    student = User.query.get_or_404(id)
    student.is_banned = not student.is_banned
    db.session.commit()
    status = "banned" if student.is_banned else "unbanned"
    flash(f'Student {student.username} {status}.', 'warning')
    return redirect(url_for('tutor.manage_students'))

@tutor_bp.route('/delete_student/<int:id>', methods=['POST'])
@tutor_required
def delete_student(id):
    from models import db, User
    student = User.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {id} account deleted.', 'danger')
    return redirect(url_for('tutor.manage_students'))

@tutor_bp.route('/delete_account', methods=['POST'])
@tutor_required
def delete_account():
    from models import db, User
    tutor_name = session.get('tutor_name')
    user = User.query.filter_by(username=tutor_name, role='Tutor').first()
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash('Your tutor account has been permanently deleted.', 'info')
        return redirect(url_for('home'))
    return redirect(url_for('tutor.dashboard'))
