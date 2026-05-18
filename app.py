from flask import Flask, render_template
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


# CREATE DATABASE
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run()