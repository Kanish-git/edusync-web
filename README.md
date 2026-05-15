# EduSync – Phase 1: Project Setup

## Folder Structure

```
edusync/
│
├── app.py                  # Main Flask application
├── database.py             # DB initialization & connection helper
├── requirements.txt        # Python dependencies
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py      # Login / Logout for both portals
│   ├── tutor_routes.py     # Tutor dashboard & features
│   └── student_routes.py   # Student dashboard & features
│
├── templates/
│   ├── base.html           # Shared navbar, flash messages, Bootstrap
│   ├── index.html          # Home page – portal selection
│   ├── tutor/
│   │   ├── login.html
│   │   └── dashboard.html
│   └── student/
│       ├── login.html
│       └── dashboard.html
│
└── static/
    ├── css/                # (for custom CSS in later phases)
    └── js/                 # (for custom JS in later phases)
```

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000
```

## Demo Credentials

| Portal  | Field           | Value         |
|---------|-----------------|---------------|
| Tutor   | Username        | admin         |
| Tutor   | Password        | admin123      |
| Student | Name            | Test Student  |
| Student | Register Number | REG001        |

## Database

- SQLite file: `edusync.db` (auto-created on first run)
- Tables: `tutors`, `students`, `assignments`, `submissions`

## What's Next (Phase 2)

- Tutor: Post assignments with topic + description
- Student: Submit assignment answers
- Tutor: View and evaluate submissions
- Performance percentage calculation
