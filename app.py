from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# TUTOR LOGIN
# =========================
@app.route("/tutor-login", methods=["GET", "POST"])
def tutor_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin":
            return redirect("/tutor-dashboard")
        return "Invalid Tutor Login"
    return render_template("login_tutor.html")

# TUTOR DASHBOARD
@app.route("/tutor-dashboard")
def tutor_dashboard():
    return render_template("tutor_dashboard.html")

# REGISTER TUTOR
@app.route("/register-tutor", methods=["GET", "POST"])
def register_tutor():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # TODO: Save to database
        return redirect("/tutor-login")
    return render_template("register_tutor.html")

# =========================
# STUDENT LOGIN
# =========================
@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        username = request.form.get("username")
        register_number = request.form.get("register_number")
        if username and register_number:
            return redirect("/student-dashboard")
        return "Invalid Student Login"
    return render_template("login_student.html")

# STUDENT DASHBOARD
@app.route("/student-dashboard")
def student_dashboard():
    return render_template("student_dashboard.html")

# REGISTER STUDENT
@app.route("/register-student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        username = request.form.get("username")
        register_number = request.form.get("register_number")
        # TODO: Save to database
        return redirect("/student-login")
    return render_template("register_student.html")

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)