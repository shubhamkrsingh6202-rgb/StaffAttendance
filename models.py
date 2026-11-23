from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(120), nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    login_time = db.Column(db.Time)
    logout_time = db.Column(db.Time)
