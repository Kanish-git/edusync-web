import os
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
from database import get_db

student_bp = Blueprint('student', __name__)

def student_required(f):
    """Decorator to protect student routes."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            flash('Please log in as a student.', 'warning')
            return redirect(url_for('auth.login_student'))
        return f(*args, **kwargs)
    return decorated

@student_bp.route('/dashboard')
@student_required
def dashboard():
    from models import Assignment, Submission, User
    from datetime import date
    
    # Check verification status
    student = User.query.get(session['student_id'])
    if not student.is_verified:
        return render_template('student/not_verified.html')
        
    today = date.today().isoformat()
    sub = None  # Fix UnboundLocalError

    # Get current assignment (where today is between start and end date)
    assignment = Assignment.query.filter(
        Assignment.start_date <= today, 
        Assignment.end_date >= today
    ).order_by(Assignment.created_at.desc()).first()

    # Check if student already submitted current assignment
    submitted = False
    if assignment:
        sub = Submission.query.filter_by(
            student_id=session['student_id'], 
            assignment_id=assignment.id
        ).first()
        submitted = sub is not None

    # Get student stats
    total_available = Assignment.query.count()
    completed_count = Submission.query.filter_by(student_id=session['student_id']).count()
    
    stats = {
        'total_available': total_available,
        'completed': completed_count,
        'pending': total_available - completed_count
    }

    return render_template('student/dashboard.html', assignment=assignment, submitted=submitted, sub=sub, stats=stats)

@student_bp.route('/submit/<int:assignment_id>', methods=['GET', 'POST'])
@student_required
def submit_assignment(assignment_id):
    from models import db, Assignment, Submission
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Safety checks
    if not assignment.is_active:
        flash('This assignment is closed for submissions.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    existing_sub = Submission.query.filter_by(
        student_id=session['student_id'], 
        assignment_id=assignment.id
    ).first()
    if existing_sub:
        flash('You have already submitted this assignment.', 'info')
        return redirect(url_for('student.dashboard'))
        
    if request.method == 'POST':
        answer = request.form.get('answer')
        attachment_path = None
        
        file = request.files.get('attachment')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            attachment_path = filename
            
        if not answer and not attachment_path:
            flash('Please provide an answer or upload a file.', 'warning')
        else:
            new_submission = Submission(
                student_id=session['student_id'],
                assignment_id=assignment.id,
                answer=answer or "",
                attachment_path=attachment_path
            )
            db.session.add(new_submission)
            db.session.commit()
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('student.dashboard'))
            
    return render_template('student/submit_assignment.html', assignment=assignment)
