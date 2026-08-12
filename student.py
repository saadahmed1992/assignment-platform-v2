from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    current_app, send_from_directory, abort
)
from flask_login import login_required, current_user

from extensions import db
from models import Assignment, Submission
from utils import allowed_file, save_upload, delete_upload, student_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    assignments = Assignment.query.order_by(Assignment.deadline.asc()).all()

    rows = []
    for a in assignments:
        submission = a.submission_for(current_user.id)
        if submission is None:
            status = "Not Submitted"
        else:
            status = submission.status
        rows.append({"assignment": a, "submission": submission, "status": status})

    return render_template("student_dashboard.html", rows=rows)


@student_bp.route("/assignment/<int:assignment_id>", methods=["GET", "POST"])
@login_required
@student_required
def assignment_detail(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    submission = assignment.submission_for(current_user.id)

    if request.method == "POST":
        if assignment.is_past_deadline:
            flash("The deadline for this assignment has passed. You can no longer submit.", "danger")
            return redirect(url_for("student.assignment_detail", assignment_id=assignment.id))

        comment = request.form.get("comment", "").strip()
        uploaded_file = request.files.get("file")

        stored_name, original_name = None, None
        if uploaded_file and uploaded_file.filename:
            if not allowed_file(uploaded_file.filename):
                flash("File type not allowed.", "danger")
                return redirect(url_for("student.assignment_detail", assignment_id=assignment.id))
            stored_name, original_name = save_upload(
                uploaded_file, current_app.config["SUBMISSION_UPLOAD_FOLDER"]
            )
        elif submission is None:
            flash("Please attach a file for your submission.", "danger")
            return redirect(url_for("student.assignment_detail", assignment_id=assignment.id))

        if submission is None:
            submission = Submission(
                assignment_id=assignment.id,
                student_id=current_user.id,
                file=stored_name,
                original_filename=original_name,
                comment=comment,
                submitted_at=datetime.utcnow(),
            )
            db.session.add(submission)
        else:
            # Replace an existing submission (only allowed before the deadline).
            if stored_name:
                delete_upload(current_app.config["SUBMISSION_UPLOAD_FOLDER"], submission.file)
                submission.file = stored_name
                submission.original_filename = original_name
            submission.comment = comment
            submission.submitted_at = datetime.utcnow()
            # Resubmitting clears a previous grade/feedback since the work changed.
            submission.grade = None
            submission.feedback = None

        db.session.commit()
        flash("Your submission has been saved.", "success")
        return redirect(url_for("student.assignment_detail", assignment_id=assignment.id))

    return render_template("assignment.html", assignment=assignment, submission=submission)


@student_bp.route("/assignment/<int:assignment_id>/attachment")
@login_required
@student_required
def download_attachment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if not assignment.attachment:
        abort(404)
    return send_from_directory(
        current_app.config["ASSIGNMENT_UPLOAD_FOLDER"],
        assignment.attachment,
        as_attachment=True,
        download_name=assignment.attachment_original_name or assignment.attachment,
    )


@student_bp.route("/submission/<int:submission_id>/file")
@login_required
@student_required
def download_own_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.student_id != current_user.id:
        abort(403)
    if not submission.file:
        abort(404)
    return send_from_directory(
        current_app.config["SUBMISSION_UPLOAD_FOLDER"],
        submission.file,
        as_attachment=True,
        download_name=submission.original_filename or submission.file,
    )
