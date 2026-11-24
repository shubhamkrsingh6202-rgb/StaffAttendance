import os
import csv
from io import StringIO
from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlalchemy import or_

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import Attendance, Staff, db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///staff_attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

KOLKATA = ZoneInfo("Asia/Kolkata")


def kolkata_now():
    """Get the current time in Kolkata as a timezone-aware datetime."""
    return datetime.now(KOLKATA)


def kolkata_today():
    """Get today's date in Kolkata."""
    return kolkata_now().date()


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
    staff_member = get_signed_in_staff()
    if staff_member is not None:
        if staff_member.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if staff_member.role == "staff":
            return redirect(url_for("staff_dashboard"))
    elif session.get("staff_id") is not None:
        session.clear()

    return render_template("home.html")


def login_for_role(role):
    if session.get("staff_id") is not None and session.get("role") != role:
        session.clear()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        staff_member = Staff.query.filter_by(email=email).first()

        if staff_member is None or not check_password_hash(
            staff_member.password_hash, password
        ):
            flash("Incorrect email or password.", "danger")
        elif staff_member.role != role:
            if role == "admin":
                flash(
                    "This account is not an admin account. Please use Staff Login.",
                    "danger",
                )
            else:
                flash(
                    "This is an admin account. Please use Admin Login.",
                    "danger",
                )
        else:
            session.clear()
            session["staff_id"] = staff_member.id
            session["staff_name"] = staff_member.name
            session["role"] = staff_member.role
            dashboard = "admin_dashboard" if role == "admin" else "staff_dashboard"
            return redirect(url_for(dashboard))

    return render_template("login.html", role=role)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    return login_for_role("admin")


@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    return login_for_role("staff")


@app.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    role = session.get("role")
    session.clear()
    flash("You have been logged out.", "success")
    if role == "admin":
        return redirect(url_for("admin_login"))
    if role == "staff":
        return redirect(url_for("staff_login"))
    return redirect(url_for("home"))


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
        return redirect(url_for("staff_login"))

    today = kolkata_today()
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
            ended_at = (
                datetime.combine(row.date, row.logout_time).replace(tzinfo=KOLKATA)
                if row.logout_time
                else kolkata_now()
            )
            started_at = started_at.replace(tzinfo=KOLKATA)
            total_hours = max(0, int((ended_at - started_at).total_seconds()))
        history.append((row, total_hours))

    checkin_datetime = (
        open_checkin.login_time.strftime("%H:%M:%S")
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
        return redirect(url_for("staff_login"))

    today = kolkata_today()
    open_checkin = Attendance.query.filter_by(
        staff_id=staff_member.id, date=today, logout_time=None
    ).first()
    if open_checkin:
        flash("You are already checked in today.", "warning")
    else:
        db.session.add(
            Attendance(
                staff_id=staff_member.id,
                date=today,
                login_time=kolkata_now().replace(tzinfo=None).time(),
            )
        )
        db.session.commit()
        flash("You have checked in.", "success")
    return redirect(url_for("staff_dashboard"))


@app.route("/staff/check-out", methods=["POST"])
def check_out():
    staff_member = get_signed_in_staff()
    if staff_member is None or staff_member.role != "staff":
        session.clear()
        return redirect(url_for("staff_login"))

    open_checkin = (
        Attendance.query.filter_by(
            staff_id=staff_member.id, date=kolkata_today(), logout_time=None
        )
        .order_by(Attendance.login_time.desc(), Attendance.id.desc())
        .first()
    )
    if open_checkin is None:
        flash("There is no open check-in to check out from.", "warning")
    else:
        open_checkin.logout_time = kolkata_now().replace(tzinfo=None).time()
        db.session.commit()
        flash("You have checked out.", "success")
    return redirect(url_for("staff_dashboard"))


@app.route("/admin")
def admin_dashboard():
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("admin_login"))

    today = kolkata_today()
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
        return redirect(url_for("admin_login"))

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
        return redirect(url_for("admin_login"))

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


@app.route("/admin/staff/<int:staff_id>/edit", methods=["POST"])
def edit_staff(staff_id):
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("admin_login"))

    staff_member = db.session.get(Staff, staff_id)
    if staff_member is None:
        flash("That staff member could not be found.", "danger")
        return redirect(url_for("admin_dashboard"))
    if staff_member.role == "admin":
        flash("Admin accounts cannot be edited.", "danger")
        return redirect(url_for("admin_dashboard"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    department = request.form.get("department", "").strip()
    new_password = request.form.get("password", "")

    if not all((name, email, department)):
        flash("Name, email, and department are required.", "danger")
        return redirect(url_for("admin_dashboard"))

    existing = Staff.query.filter(
        db.func.lower(Staff.email) == email,
        Staff.id != staff_member.id,
    ).first()
    if existing:
        flash("That email already belongs to another staff member.", "danger")
        return redirect(url_for("admin_dashboard"))

    staff_member.name = name
    staff_member.email = email
    staff_member.department = department
    if new_password:
        staff_member.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash(f"{name} was updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))


def get_filtered_attendance():
    """Build a filtered list of attendance rows for the reports page."""
    staff_id = request.args.get("staff_id", "").strip()
    from_date_text = request.args.get("from_date", "").strip()
    to_date_text = request.args.get("to_date", "").strip()
    search_text = request.args.get("search", "").strip()

    rows = (
        Attendance.query.join(Staff, Attendance.staff_id == Staff.id)
        .add_entity(Staff)
    )

    if staff_id:
        try:
            rows = rows.filter(Attendance.staff_id == int(staff_id))
        except ValueError:
            pass
    if from_date_text:
        try:
            rows = rows.filter(Attendance.date >= date.fromisoformat(from_date_text))
        except ValueError:
            pass
    if to_date_text:
        try:
            rows = rows.filter(Attendance.date <= date.fromisoformat(to_date_text))
        except ValueError:
            pass
    if search_text:
        pattern = f"%{search_text}%"
        rows = rows.filter(
            or_(
                Staff.name.ilike(pattern),
                Staff.department.ilike(pattern),
            )
        )

    return (
        rows.order_by(Attendance.date.desc(), Attendance.login_time.desc(), Attendance.id.desc())
        .all()
    )


def format_working_seconds(row):
    """Return elapsed seconds for one attendance row."""
    if row.login_time is None:
        return 0
    started = datetime.combine(row.date, row.login_time).replace(tzinfo=KOLKATA)
    ended = (
        datetime.combine(row.date, row.logout_time).replace(tzinfo=KOLKATA)
        if row.logout_time
        else kolkata_now()
    )
    return max(0, int((ended - started).total_seconds()))


@app.route("/admin/reports")
def admin_reports():
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("admin_login"))

    staff_members = Staff.query.filter_by(role="staff").order_by(Staff.name).all()
    joined_rows = get_filtered_attendance()

    report_rows = []
    total_seconds = 0
    present_staff_ids = set()
    for attendance_row, staff_member in joined_rows:
        seconds = format_working_seconds(attendance_row)
        total_seconds += seconds
        present_staff_ids.add(attendance_row.staff_id)
        report_rows.append((attendance_row, staff_member, seconds))

    return render_template(
        "reports.html",
        staff_members=staff_members,
        report_rows=report_rows,
        total_records=len(report_rows),
        total_seconds=total_seconds,
        present_count=len(present_staff_ids),
        filters={
            "staff_id": request.args.get("staff_id", ""),
            "from_date": request.args.get("from_date", ""),
            "to_date": request.args.get("to_date", ""),
            "search": request.args.get("search", ""),
        },
    )


@app.route("/admin/reports/export")
def export_admin_reports():
    admin = get_signed_in_staff()
    if admin is None or admin.role != "admin":
        session.clear()
        return redirect(url_for("admin_login"))

    joined_rows = get_filtered_attendance()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Department", "Date", "Check In", "Check Out", "Total Hours"])

    for attendance_row, staff_member in joined_rows:
        seconds = format_working_seconds(attendance_row)
        if attendance_row.logout_time is None:
            total_hours = "Still working"
        else:
            total_hours = (
                f"{seconds // 3600:02d}:"
                f"{(seconds % 3600) // 60:02d}:"
                f"{seconds % 60:02d}"
            )
        writer.writerow([
            staff_member.name,
            staff_member.email,
            staff_member.department,
            attendance_row.date.isoformat(),
            attendance_row.login_time.strftime("%I:%M:%S %p") if attendance_row.login_time else "",
            attendance_row.logout_time.strftime("%I:%M:%S %p") if attendance_row.logout_time else "",
            total_hours,
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"},
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=True, port=5000)
