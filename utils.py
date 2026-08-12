import os
import uuid
from functools import wraps

from flask import current_app, abort
from flask_login import current_user


def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def save_upload(file_storage, folder):
    """Save an uploaded file with a random-prefixed name to avoid collisions.
    Returns (stored_filename, original_filename) or (None, None) if no file.
    """
    if not file_storage or file_storage.filename == "":
        return None, None

    original_name = file_storage.filename
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    stored_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, stored_name))
    return stored_name, original_name


def delete_upload(folder, stored_filename):
    if not stored_filename:
        return
    path = os.path.join(folder, stored_filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def instructor_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_instructor:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped


def student_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped
