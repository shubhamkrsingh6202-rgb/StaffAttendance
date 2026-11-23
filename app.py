import os
from datetime import date, datetime

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


def get_signed_in_staff():
    staff_id = session.get("staff_id")
    if staff_id is None:
        return None
    return db.session.get(Staff, staff_id)


@app.route("/staff")
def staff_dashboard():
    staff_member = get_signed_in_staff()
    if staff_member is None or staff_member.role != "staff":
        session.clear()
        return redirect(url_for("login"))

    today = date.today()
    attendance_rows = (
        Attendance.query.filter_by(staff_id=staff_member.id)
        .order_by(Attendance.date.desc(), Attendance.login_time.desc(), Attendance.id.desc())
        .limit(10)
        .all()
    )
    open_checkin = (
        Attendance.query.filter_by(
            staff_id=staff_member.id, date=today, logout_time=None
        )
        .order_by(Attendance.login_time.desc(), Attendance.id.desc())
        .first()
    )
    history = []
    for row in attendance_rows:
        total_hours = None
        if row.login_time:
            started_at = datetime.combine(row.date, row.login_time)
            ended_at = datetime.combine(row.date, row.logout_time) if row.logout_time else datetime.now()
            total_hours = max(0, int((ended_at - started_at).total_seconds()))
        history.append((row, total_hours))

    checkin_datetime = (
        datetime.combine(open_checkin.date, open_checkin.login_time).isoformat(
            timespec="seconds"
        )
        if open_checkin and open_checkin.login_time
        else None
    )
    if open_checkin:
        today_status = "Checked In"
    elif any(row.date == today for row in attendance_rows):
        today_status = "Checked Out"
    else:
        today_status = "Absent"
    return render_template(
        "staff_dashboard.html",
        staff_member=staff_member,
        today=today,
        history=history,
        is_checked_in=open_checkin is not None,
        checkin_datetime=checkin_datetime,
        today_status=today_status,
    )


@app.route("/staff/check-in", methods=["POST"])
def check_in():
    staff_member = get_signed_in_staff()
    if staff_member is None or staff_member.role != "staff":
        session.clear()
        return redirect(url_for("login"))

    today = date.today()
    open_checkin = Attendance.query.filter_by(
        staff_id=staff_member.id, date=today, logout_time=None
    ).first()
    if open_checkin:
        flash("You are already checked in today.", "warning")
    else:
        db.session.add(
            Attendance(staff_id=staff_member.id, date=today, login_time=datetime.now().time())
        )
        db.session.commit()
        flash("You have checked in.", "success")
    return redirect(url_for("staff_dashboard"))


@app.route("/staff/check-out", methods=["POST"])
def check_out():
    staff_member = get_signed_in_staff()
    if staff_member is None or staff_member.role != "staff":
        session.clear()
        return redirect(url_for("login"))

    open_checkin = (
        Attendance.query.filter_by(
            staff_id=staff_member.id, date=date.today(), logout_time=None
        )
        .order_by(Attendance.login_time.desc(), Attendance.id.desc())
        .first()
    )
    if open_checkin is None:
        flash("There is no open check-in to check out from.", "warning")
    else:
        open_checkin.logout_time = datetime.now().time()
        db.session.commit()
        flash("You have checked out.", "success")
    return redirect(url_for("staff_dashboard"))


@app.route("/admin")
def admin_dashboard():
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("login"))

    today = date.today()
    staff_members = Staff.query.filter_by(role="staff").order_by(Staff.name).all()
    today_rows = (
        Attendance.query.filter_by(date=today)
        .order_by(Attendance.login_time.desc(), Attendance.id.desc())
        .all()
    )
    staff_ids = {staff_member.id for staff_member in staff_members}
    latest_by_staff = {}
    for row in today_rows:
        if row.staff_id in staff_ids:
            latest_by_staff.setdefault(row.staff_id, row)
    checked_in_ids = {
        staff_id
        for staff_id, row in latest_by_staff.items()
        if row.logout_time is None
    }

    absent_today = len(staff_members) - len(latest_by_staff)
    return render_template(
        "admin_dashboard.html",
        staff_members=staff_members,
        latest_by_staff=latest_by_staff,
        total_staff=len(staff_members),
        currently_checked_in=len(checked_in_ids),
        absent_today=absent_today,
        today=today,
    )


@app.route("/admin/staff/add", methods=["POST"])
def add_staff():
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    department = request.form.get("department", "").strip()
    password = request.form.get("password", "")

    if not all((name, email, department, password)):
        flash("Please complete all staff fields.", "danger")
    elif db.session.query(Staff.id).filter(db.func.lower(Staff.email) == email).first():
        flash("A staff account with that email already exists.", "danger")
    else:
        staff_member = Staff(
            name=name,
            email=email,
            department=department,
            password_hash=generate_password_hash(password),
            role="staff",
        )
        db.session.add(staff_member)
        db.session.commit()
        flash(f"{name} was added successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/staff/<int:staff_id>/delete", methods=["POST"])
def delete_staff(staff_id):
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("login"))

    staff_member = db.session.get(Staff, staff_id)
    if staff_member is None:
        flash("That staff member could not be found.", "danger")
    elif staff_member.role == "admin":
        flash("Admin accounts cannot be deleted.", "danger")
    else:
        Attendance.query.filter_by(staff_id=staff_member.id).delete()
        db.session.delete(staff_member)
        db.session.commit()
        flash(f"{staff_member.name} was deleted.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    create_database()
    app.run(debug=True, port=5000)
