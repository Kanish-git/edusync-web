from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=True) # Tutors
    register_number = db.Column(db.String(50), unique=True, nullable=True) # Students
    role = db.Column(db.String(10), nullable=False) # 'Tutor' or 'Student'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100), nullable=False)
    task_description = db.Column(db.Text, nullable=False)
    document_path = db.Column(db.String(200), nullable=True)
    date_uploaded = db.Column(db.DateTime, default=db.func.current_timestamp())

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(80), nullable=False)
    register_number = db.Column(db.String(50), nullable=False)
    topic_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Cleared")
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())