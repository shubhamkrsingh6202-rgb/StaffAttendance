import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import Attendance, Staff, db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///staff_attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def create_database():
    """Create the tables and add the default admin on the first run."""
    os.makedirs(app.instance_path, exist_ok=True)

    with app.app_context():
        db.create_all()

        admin = Staff.query.filter_by(email="admin@college.com").first()
        if admin is None:
            admin = Staff(
                name="Administrator",
                email="admin@college.com",
                password_hash=generate_password_hash("admin123"),
                role="admin",
                department="Administration",
            )
            db.session.add(admin)
            db.session.commit()


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        staff_member = Staff.query.filter_by(email=email).first()

        if staff_member and check_password_hash(staff_member.password_hash, password):
            session["staff_id"] = staff_member.id
            session["staff_name"] = staff_member.name
            session["role"] = staff_member.role

            if staff_member.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("staff_dashboard"))

        flash("Incorrect email or password. Please try again.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/staff")
def staff_dashboard():
    if "staff_id" not in session:
        return redirect(url_for("login"))
    return render_template("staff_dashboard.html")


@app.route("/admin")
def admin_dashboard():
    if "staff_id" not in session:
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")


if __name__ == "__main__":
    create_database()
    app.run(debug=True, port=5000)
