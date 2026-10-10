from flask import Blueprint, request, jsonify
from services.settings_service import SettingsService

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
def get_settings():
    """Retrieve user study settings."""
    settings = SettingsService.get_settings()
    return jsonify({
        "success": True,
        "data": settings.to_dict()
    }), 200

@settings_bp.route('', methods=['PUT'])
def update_settings():
    """Update user study settings."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON or empty body."
        }), 400

    updated_settings, error = SettingsService.update_settings(data)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    return jsonify({
        "success": True,
        "message": "Settings updated successfully.",
        "data": updated_settings.to_dict()
    }), 200
