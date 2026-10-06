from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=True) # Tutors
    register_number = db.Column(db.String(50), unique=True, nullable=True) # Students
    role = db.Column(db.String(10), nullable=False) # 'Tutor' or 'Student'
    is_verified = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100), nullable=False)
    task_description = db.Column(db.Text, nullable=False)
    document_path = db.Column(db.String(200), nullable=True)
    deadline = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(50), default="Computer Science")
    difficulty = db.Column(db.String(20), default="Intermediate")
    max_marks = db.Column(db.Integer, default=100)
    priority = db.Column(db.String(20), default="Standard")
    date_uploaded = db.Column(db.DateTime, default=db.func.current_timestamp())

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(80), nullable=False)
    register_number = db.Column(db.String(50), nullable=False)
    topic_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Cleared") # 'Cleared', 'pending', 'failed'
    score = db.Column(db.String(20), nullable=True) # e.g. '95/100' or 'A+'
    feedback = db.Column(db.Text, nullable=True)
    submission_text = db.Column(db.Text, nullable=True) # Student solution code/text
    submission_file = db.Column(db.String(200), nullable=True) # Student uploaded solution file
    student_notes = db.Column(db.Text, nullable=True) # Student notes to tutor
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), default="info") # 'info', 'warning', 'urgent', 'success'
    posted_by = db.Column(db.String(80), default="Tutor")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

def ensure_db_schema(app):
    """Ensure all tables and columns exist in SQLite database safely."""
    with app.app_context():
        db.create_all()
        try:
            with db.engine.connect() as conn:
                # Check assignment columns
                assign_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(assignment)")).fetchall()]
                if 'category' not in assign_cols:
                    conn.execute(text("ALTER TABLE assignment ADD COLUMN category VARCHAR(50) DEFAULT 'Computer Science'"))
                if 'difficulty' not in assign_cols:
                    conn.execute(text("ALTER TABLE assignment ADD COLUMN difficulty VARCHAR(20) DEFAULT 'Intermediate'"))
                if 'max_marks' not in assign_cols:
                    conn.execute(text("ALTER TABLE assignment ADD COLUMN max_marks INTEGER DEFAULT 100"))
                if 'priority' not in assign_cols:
                    conn.execute(text("ALTER TABLE assignment ADD COLUMN priority VARCHAR(20) DEFAULT 'Standard'"))

                # Check submission columns
                sub_cols = [r[1] for r in conn.execute(text("PRAGMA table_info(submission)")).fetchall()]
                if 'score' not in sub_cols:
                    conn.execute(text("ALTER TABLE submission ADD COLUMN score VARCHAR(20)"))
                if 'feedback' not in sub_cols:
                    conn.execute(text("ALTER TABLE submission ADD COLUMN feedback TEXT"))
                if 'submission_text' not in sub_cols:
                    conn.execute(text("ALTER TABLE submission ADD COLUMN submission_text TEXT"))
                if 'submission_file' not in sub_cols:
                    conn.execute(text("ALTER TABLE submission ADD COLUMN submission_file VARCHAR(200)"))
                if 'student_notes' not in sub_cols:
                    conn.execute(text("ALTER TABLE submission ADD COLUMN student_notes TEXT"))

                conn.commit()
        except Exception as e:
            print("Schema migration note:", e)