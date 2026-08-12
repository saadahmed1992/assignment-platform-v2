from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Public registration creates Student accounts only.
        # Instructor accounts are created separately and are never
        # exposed as a registration option.

        error = None

        if not name or not email or not password or not confirm_password:
            error = "All fields are required."

        elif len(password) < 8:
            error = "Password must be at least 8 characters."

        elif not any(char.isupper() for char in password):
            error = "Password must contain at least one uppercase letter."

        elif not any(char.islower() for char in password):
            error = "Password must contain at least one lowercase letter."

        elif not any(char.isdigit() for char in password):
            error = "Password must contain at least one number."

        elif not any(not char.isalnum() for char in password):
            error = "Password must contain at least one special character."

        elif password != confirm_password:
            error = "Passwords do not match."

        elif User.query.filter_by(email=email).first():
            error = "An account with this email already exists."

        if error:
            flash(error, "danger")
            return render_template(
                "register.html",
                name=name,
                email=email
            )

        user = User(
            name=name,
            email=email,
            role="student"
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))