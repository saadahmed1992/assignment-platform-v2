from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    current_app, send_from_directory, abort
)
from flask_login import login_required, current_user

from extensions import db
from models import User, Assignment, Submission
from utils import allowed_file, save_upload, delete_upload, instructor_required

instructor_bp = Blueprint("instructor", __name__, url_prefix="/instructor")


@instructor_bp.route("/dashboard")
@login_required
@instructor_required
def dashboard():
    total_students = User.query.filter_by(role="student").count()
    total_assignments = Assignment.query.count()
    total_submissions = Submission.query.count()
    pending_submissions = Submission.query.filter(Submission.grade.is_(None)).count()

    assignments = Assignment.query.order_by(Assignment.deadline.asc()).all()
    rows = []
    for a in assignments:
        rows.append({
            "assignment": a,
            "submission_count": len(a.submissions),
            "student_count": total_students,
        })

    return render_template(
        "instructor_dashboard.html",
        total_students=total_students,
        total_assignments=total_assignments,
        total_submissions=total_submissions,
        pending_submissions=pending_submissions,
        rows=rows,
    )


@instructor_bp.route("/assignments/new", methods=["GET", "POST"])
@login_required
@instructor_required
def create_assignment():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        deadline_str = request.form.get("deadline", "")
        max_grade = request.form.get("max_grade", "").strip()
        uploaded_file = request.files.get("attachment")

        error = None
        deadline = None
        if not title or not description or not deadline_str or not max_grade:
            error = "Please fill in all required fields."
        else:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                error = "Invalid deadline format."
            if not max_grade.isdigit() or int(max_grade) <= 0:
                error = "Maximum grade must be a positive number."

        if uploaded_file and uploaded_file.filename and not allowed_file(uploaded_file.filename):
            error = "Attachment file type is not allowed."

        if error:
            flash(error, "danger")
            return render_template("create_assignment.html", form=request.form)

        stored_name, original_name = save_upload(
            uploaded_file, current_app.config["ASSIGNMENT_UPLOAD_FOLDER"]
        )

        assignment = Assignment(
            title=title,
            description=description,
            deadline=deadline,
            max_grade=int(max_grade),
            attachment=stored_name,
            attachment_original_name=original_name,
        )
        db.session.add(assignment)
        db.session.commit()

        flash("Assignment created successfully.", "success")
        return redirect(url_for("instructor.dashboard"))

    return render_template("create_assignment.html", form={})


@instructor_bp.route("/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
@login_required
@instructor_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        deadline_str = request.form.get("deadline", "")
        max_grade = request.form.get("max_grade", "").strip()
        uploaded_file = request.files.get("attachment")
        remove_attachment = request.form.get("remove_attachment") == "on"

        error = None
        deadline = None
        if not title or not description or not deadline_str or not max_grade:
            error = "Please fill in all required fields."
        else:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                error = "Invalid deadline format."
            if not max_grade.isdigit() or int(max_grade) <= 0:
                error = "Maximum grade must be a positive number."

        if uploaded_file and uploaded_file.filename and not allowed_file(uploaded_file.filename):
            error = "Attachment file type is not allowed."

        if error:
            flash(error, "danger")
            return render_template("edit_assignment.html", assignment=assignment)

        assignment.title = title
        assignment.description = description
        assignment.deadline = deadline
        assignment.max_grade = int(max_grade)

        if remove_attachment and assignment.attachment and not (uploaded_file and uploaded_file.filename):
            delete_upload(current_app.config["ASSIGNMENT_UPLOAD_FOLDER"], assignment.attachment)
            assignment.attachment = None
            assignment.attachment_original_name = None

        if uploaded_file and uploaded_file.filename:
            delete_upload(current_app.config["ASSIGNMENT_UPLOAD_FOLDER"], assignment.attachment)
            stored_name, original_name = save_upload(
                uploaded_file, current_app.config["ASSIGNMENT_UPLOAD_FOLDER"]
            )
            assignment.attachment = stored_name
            assignment.attachment_original_name = original_name

        db.session.commit()
        flash("Assignment updated successfully.", "success")
        return redirect(url_for("instructor.dashboard"))

    return render_template("edit_assignment.html", assignment=assignment)


@instructor_bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@login_required
@instructor_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    delete_upload(current_app.config["ASSIGNMENT_UPLOAD_FOLDER"], assignment.attachment)
    for submission in assignment.submissions:
        delete_upload(current_app.config["SUBMISSION_UPLOAD_FOLDER"], submission.file)

    db.session.delete(assignment)
    db.session.commit()

    flash("Assignment deleted.", "info")
    return redirect(url_for("instructor.dashboard"))


@instructor_bp.route("/assignments/<int:assignment_id>/submissions")
@login_required
@instructor_required
def view_submissions(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    students = User.query.filter_by(role="student").order_by(User.name.asc()).all()

    rows = []
    for student in students:
        submission = assignment.submission_for(student.id)
        status = "Not Submitted" if submission is None else submission.status
        rows.append({"student": student, "submission": submission, "status": status})

    return render_template("submissions.html", assignment=assignment, rows=rows)


@instructor_bp.route("/submissions/<int:submission_id>", methods=["GET", "POST"])
@login_required
@instructor_required
def submission_details(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment

    if request.method == "POST":
        grade = request.form.get("grade", "").strip()
        feedback = request.form.get("feedback", "").strip()

        error = None
        if grade:
            if not grade.isdigit() or int(grade) < 0 or int(grade) > assignment.max_grade:
                error = f"Grade must be a number between 0 and {assignment.max_grade}."

        if error:
            flash(error, "danger")
            return render_template("submission_details.html", submission=submission, assignment=assignment)

        submission.grade = int(grade) if grade else None
        submission.feedback = feedback
        db.session.commit()

        flash("Grade and feedback saved.", "success")
        return redirect(url_for("instructor.view_submissions", assignment_id=assignment.id))

    return render_template("submission_details.html", submission=submission, assignment=assignment)


@instructor_bp.route("/students")
@login_required
@instructor_required
def students():
    all_students = User.query.filter_by(role="student").order_by(User.name.asc()).all()
    return render_template("students.html", students=all_students)


@instructor_bp.route("/submission/<int:submission_id>/file")
@login_required
@instructor_required
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if not submission.file:
        abort(404)
    return send_from_directory(
        current_app.config["SUBMISSION_UPLOAD_FOLDER"],
        submission.file,
        as_attachment=True,
        download_name=submission.original_filename or submission.file,
    )


@instructor_bp.route("/assignments/<int:assignment_id>/attachment")
@login_required
@instructor_required
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
