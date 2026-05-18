from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# DATABASE
basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///" + os.path.join(basedir, "database.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# MODEL
class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    student_name = db.Column(db.String(100))

    register_number = db.Column(db.String(50))

    status = db.Column(db.String(50))


# HOME
@app.route("/")
def home():

    students = Student.query.all()

    return render_template(
        "index.html",
        students=students
    )


# ADD STUDENT
@app.route("/add", methods=["POST"])
def add_student():

    name = request.form["student_name"]

    reg = request.form["register_number"]

    status = request.form["status"]

    new_student = Student(
        student_name=name,
        register_number=reg,
        status=status
    )

    db.session.add(new_student)

    db.session.commit()

    return redirect("/")


# CREATE DATABASE
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run()