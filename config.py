import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _resolve_database_uri():
    """Use Railway's PostgreSQL DATABASE_URL when present, otherwise fall
    back to a local SQLite file for development.
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Railway (and some other hosts) hand out "postgres://", but
        # SQLAlchemy's psycopg2 driver requires "postgresql://".
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    return "sqlite:///" + os.path.join(BASE_DIR, "database", "app.db")


class Config:
    BASE_DIR = BASE_DIR

    # Change this in production; kept simple for a small class project.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Initial instructor account, auto-seeded on startup (see app.py).
    INSTRUCTOR_NAME = "Platform Instructor"
    INSTRUCTOR_EMAIL = "instructor@assignment-platform.com"
    INSTRUCTOR_PASSWORD = os.environ.get("INSTRUCTOR_PASSWORD", "ChangeThisPassword123!")

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ASSIGNMENT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "assignments")
    SUBMISSION_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "submissions")

    # 16 MB max upload size (covers PDFs, docs, zipped folders, etc.)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "zip",
        "png", "jpg", "jpeg", "gif",
    }
