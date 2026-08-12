import os

from flask import Flask, render_template
from flask_login import current_user

from config import Config
from extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure required folders exist.
    os.makedirs(os.path.join(Config.BASE_DIR, "database"), exist_ok=True)
    os.makedirs(app.config["ASSIGNMENT_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SUBMISSION_UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def seed_instructor():
        """Create the one initial instructor account if it doesn't exist yet.

        Safe to run on every startup: it only ever checks-then-creates, so
        it never resets a password or creates a duplicate on repeat deploys.
        """
        email = app.config["INSTRUCTOR_EMAIL"]
        existing = User.query.filter_by(email=email).first()
        if existing:
            return

        instructor = User(
            name=app.config["INSTRUCTOR_NAME"],
            email=email,
            role="instructor",
        )
        instructor.set_password(app.config["INSTRUCTOR_PASSWORD"])
        db.session.add(instructor)
        db.session.commit()

    from auth import auth_bp
    from main import main_bp
    from student import student_bp
    from instructor import instructor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(instructor_bp)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="You don't have permission to access this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413, message="The uploaded file is too large."), 413

    @app.context_processor
    def inject_globals():
        return {"current_user": current_user}

    with app.app_context():
        db.create_all()
        seed_instructor()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
