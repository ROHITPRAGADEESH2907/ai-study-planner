from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def dashboard():
    """Serve the main dashboard page."""
    return render_template("dashboard.html")


@frontend_bp.route("/subjects")
def subjects():
    """Serve the subjects management page."""
    return render_template("subjects.html")


@frontend_bp.route("/topics")
def topics():
    """Serve the topics management page."""
    return render_template("topics.html")


@frontend_bp.route("/planner")
def planner():
    """Serve the study planner page."""
    return render_template("planner.html")


@frontend_bp.route("/analytics")
def analytics():
    """Serve the study analytics page."""
    return render_template("analytics.html")


@frontend_bp.route("/settings")
def settings():
    """Serve the user study settings page."""
    return render_template("settings.html")