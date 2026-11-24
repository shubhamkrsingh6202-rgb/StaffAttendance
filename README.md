# Staff Attendance

A Flask-based staff attendance management system with secure role-based login, staff administration, attendance tracking, reporting, and CSV export.

## Features

- Separate administrator and staff login portals
- Password-hashed authentication
- Staff check-in and check-out
- Admin dashboard with live attendance summaries
- Add, edit, and delete staff accounts
- Filter and search attendance reports
- CSV export for attendance records
- Kolkata (`Asia/Kolkata`) timezone support
- SQLite database storage

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Security:** Werkzeug password hashing

## Project Structure

```text
StaffAttendance/
├── app.py                  # Routes, app configuration, and business logic
├── models.py               # SQLAlchemy database models
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/style.css       # Application styles
│   └── js/main.js          # Frontend interactions
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── admin_dashboard.html
    ├── staff_dashboard.html
    └── reports.html
```

## Getting Started

### Prerequisites

- Python 3.9 or newer
- `pip`

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/shubhamkrsingh6202-rgb/StaffAttendance.git
   cd StaffAttendance
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   ```

   **Windows:**

   ```bash
   venv\Scripts\activate
   ```

   **macOS/Linux:**

   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   python app.py
   ```

5. Open <http://127.0.0.1:5000> in your browser.

The SQLite database and default administrator account are created automatically on the first run.

## Default Admin Login

- **Email:** `admin@college.com`
- **Password:** `admin123`

> **Security:** Change the default password and set a strong `SECRET_KEY` before deploying the application.

## Environment Configuration

Set the Flask session secret using an environment variable:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
```

On Windows PowerShell:

```powershell
$env:SECRET_KEY="replace-with-a-long-random-secret"
```

## Usage

### Administrator

1. Open `/admin/login` or select **Admin Login** on the home page.
2. Manage staff accounts from the admin dashboard.
3. Review today's attendance and individual status.
4. Filter attendance reports by staff, date, department, or name.
5. Export filtered records as a CSV file.

### Staff

1. Open `/staff/login` or select **Staff Login** on the home page.
2. Check in once for the day.
3. Check out when work ends.
4. View recent attendance history and working duration.

## Database

The application uses SQLite by default. SQLAlchemy creates the database under the Flask instance directory:

```text
instance/staff_attendance.db
```

The database contains:

- `Staff`: account, role, department, and password hash
- `Attendance`: staff member, date, login time, and logout time

## Running in Production

The bundled development server is suitable for local use only. For production, use a production WSGI server and a persistent secret key:

```bash
pip install gunicorn
SECRET_KEY="replace-with-a-long-random-secret" gunicorn app:app
```

Consider replacing SQLite with a managed database when deploying for concurrent users or multiple application instances.

## License

No license has been specified for this project.
