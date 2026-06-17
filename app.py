from flask import Flask, redirect, request, url_for

from config import Config
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.patient_routes import patients_bp
from routes.analysis_routes import analysis_bp
from routes.report_routes import reports_bp
from routes.user_routes import users_bp
from routes.reference_routes import references_bp
from utils import can_admin, can_edit, current_user


PUBLIC_ENDPOINTS = {
    "static",
    "auth.auth_page",
    "auth.login",
    "auth.register",
}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(references_bp)

    @app.before_request
    def require_authorization():
        endpoint = request.endpoint or ""

        if endpoint.startswith("static"):
            return None

        if endpoint in PUBLIC_ENDPOINTS:
            if endpoint == "auth.auth_page" and current_user():
                return redirect(url_for("main.index"))
            return None

        if not current_user():
            next_url = request.full_path if request.query_string else request.path
            return redirect(url_for("auth.auth_page", next=next_url))

        return None

    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "current_user": current_user(),
            "can_edit": can_edit(),
            "can_admin": can_admin(),
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
