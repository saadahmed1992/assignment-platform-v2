from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # "student" or "instructor"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship(
        "Submission", backref="student", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_instructor(self):
        return self.role == "instructor"

    @property
    def is_student(self):
        return self.role == "student"


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    max_grade = db.Column(db.Integer, nullable=False, default=100)
    attachment = db.Column(db.String(255), nullable=True)  # stored filename
    attachment_original_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship(
        "Submission", backref="assignment", lazy=True, cascade="all, delete-orphan"
    )

    def submission_for(self, student_id):
        for s in self.submissions:
            if s.student_id == student_id:
                return s
        return None

    @property
    def is_past_deadline(self):
        return datetime.utcnow() > self.deadline


class Submission(db.Model):
    __tablename__ = "submissions"
    __table_args__ = (
        db.UniqueConstraint("assignment_id", "student_id", name="one_submission_per_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    file = db.Column(db.String(255), nullable=True)  # stored filename
    original_filename = db.Column(db.String(255), nullable=True)
    comment = db.Column(db.Text, nullable=True)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    grade = db.Column(db.Integer, nullable=True)
    feedback = db.Column(db.Text, nullable=True)

    @property
    def status(self):
        if self.grade is not None:
            return "Graded"
        return "Submitted"
