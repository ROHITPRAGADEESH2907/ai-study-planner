from flask import Blueprint, jsonify
from extensions import db
from sqlalchemy import text

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint verifying application runtime status and database connectivity.
    """
    db_status = "unhealthy"
    try:
        # Perform lightweight database test query
        db.session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "ok",
        "service": "AI Study Planner API",
        "database": db_status
    }), 200
