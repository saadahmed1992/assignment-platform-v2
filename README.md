# Coursework — Assignment Submission Platform

A simple Flask + SQLite app for a small class: instructors post assignments,
students submit their work, instructors grade it.

## Architecture

- **Backend:** Flask, organized as small blueprints — `auth` (login/register),
  `main` (role-based redirect), `student` (dashboard, assignment view,
  submission), `instructor` (dashboard, assignment CRUD, grading).
- **Database:** SQLite via Flask-SQLAlchemy. Three tables: `users`,
  `assignments`, `submissions`. A submission is unique per
  `(assignment_id, student_id)` — students update their existing row instead
  of creating a new one when they resubmit before the deadline.
- **Auth:** Flask-Login with salted password hashes (Werkzeug's
  `generate_password_hash`). Two roles, `student` and `instructor`, enforced
  by `@instructor_required` / `@student_required` decorators on top of
  `@login_required`.
- **File uploads:** stored on disk under `uploads/assignments/` and
  `uploads/submissions/` with randomized filenames (the original filename is
  kept in the database for display/download). Extension allow-list and a
  16 MB size cap are enforced.
- **Frontend:** server-rendered Jinja templates with a single hand-written
  stylesheet (no build step) — a sidebar layout, status badges, cards, and
  simple tables that collapse into stacked cards on mobile.

## Project structure

```
assignment_platform/
├── app.py                  # application factory, error handlers
├── config.py                # paths, upload limits, allowed extensions
├── extensions.py            # db / login_manager singletons
├── models.py                 # User, Assignment, Submission
├── utils.py                  # file upload helpers, role decorators
├── auth.py                   # /login, /register, /logout
├── main.py                   # / and /dashboard (role redirect)
├── student.py                 # student-facing routes
├── instructor.py              # instructor-facing routes
├── templates/                 # Jinja templates
├── static/css/style.css       # all styling
├── static/js/app.js           # sidebar toggle, flash auto-dismiss
├── uploads/assignments/       # assignment attachments (created at runtime)
├── uploads/submissions/       # student submissions (created at runtime)
├── database/app.db            # SQLite file (created at runtime)
└── requirements.txt
```

## Running it locally

1. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```
   The database and upload folders are created automatically on first run.

4. **Open your browser:**
   Go to `http://127.0.0.1:5000`.

5. **Log in as the instructor, or register as a student:**
   A single instructor account is created automatically the first time the
   app starts (see "Instructor account" below) — just log in with it.
   Public registration only ever creates **student** accounts; there's no
   role picker.

## Instructor account

One instructor account is seeded automatically on startup (works locally
with SQLite and on Railway with PostgreSQL — no shell access or manual SQL
needed):

- Email: `instructor@assignment-platform.com`
- Password: `ChangeThisPassword123!`

The seed check runs every time the app starts but only ever creates this
account once — if it already exists, startup does nothing to it (no
password reset, no duplicate). To use a different password on a real
deployment, set an `INSTRUCTOR_PASSWORD` environment variable before the
first startup; after the account is created, changing that variable has no
effect (the seed step is check-then-create only).

## Notes

- This is intentionally minimal — no email verification, no password reset,
  no admin panel. It's meant for a small trusted group of students, not
  production use at scale.
- If you ever want to reset everything, stop the app and delete
  `database/app.db` (and optionally the contents of `uploads/`), then start
  the app again — it will recreate an empty database.
