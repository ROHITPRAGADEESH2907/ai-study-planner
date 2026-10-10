import os
from flask import Flask, request, jsonify
from config import config_by_name
from extensions import db
from routes.health import health_bp
from routes.settings import settings_bp
from routes.subjects import subjects_bp
from routes.topics import topics_bp
from routes.planner import planner_bp
from routes.frontend import frontend_bp
from models import UserSettings, Subject, Topic, StudySession

def create_app(config_name=None):
    """
    Application factory for the AI Study Planner Flask application.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app_config = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(app_config)
    app_config.init_app(app)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(frontend_bp)


    # Global error handlers for consistent JSON API responses
    @app.errorhandler(404)
    def not_found_handler(e):
        return jsonify({"success": False, "error": "Endpoint or resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed_handler(e):
        return jsonify({"success": False, "error": "Method not allowed for this endpoint"}), 405

    @app.errorhandler(500)
    def internal_error_handler(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    # Database setup and CLI helper
    with app.app_context():
        db.create_all()
        # Seed default user settings row if not present
        if not UserSettings.query.first():
            default_settings = UserSettings(
                weekday_hours=3.0,
                weekend_hours=6.0,
                exam_buffer_days=2
            )
            db.session.add(default_settings)
            db.session.commit()

    @app.cli.command("init-db")
    def init_db_command():
        """Creates database tables and default records."""
        db.create_all()
        if not UserSettings.query.first():
            db.session.add(UserSettings())
            db.session.commit()
        print("Database initialized successfully.")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
