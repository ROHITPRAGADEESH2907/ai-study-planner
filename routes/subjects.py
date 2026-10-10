from flask import Blueprint, request, jsonify
from services.subject_service import SubjectService

subjects_bp = Blueprint('subjects', __name__, url_prefix='/api/subjects')

@subjects_bp.route('', methods=['GET'])
def get_all_subjects():
    """Retrieve all subjects ordered by upcoming exam date."""
    subjects = SubjectService.get_all_subjects()
    return jsonify({
        "success": True,
        "count": len(subjects),
        "data": [s.to_dict() for s in subjects]
    }), 200

@subjects_bp.route('/<int:subject_id>', methods=['GET'])
def get_subject(subject_id):
    """Retrieve a single subject by ID including its topics."""
    subject = SubjectService.get_subject_by_id(subject_id)
    if not subject:
        return jsonify({
            "success": False,
            "error": f"Subject with ID {subject_id} not found."
        }), 404

    data = subject.to_dict()
    data['topics'] = [t.to_dict() for t in subject.topics]
    return jsonify({
        "success": True,
        "data": data
    }), 200

@subjects_bp.route('', methods=['POST'])
def create_subject():
    """Create a new subject."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON or empty body."
        }), 400

    subject, error = SubjectService.create_subject(data)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), 400

    return jsonify({
        "success": True,
        "message": "Subject created successfully.",
        "data": subject.to_dict()
    }), 201

@subjects_bp.route('/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    """Update an existing subject."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON or empty body."
        }), 400

    subject, error, status_code = SubjectService.update_subject(subject_id, data)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "message": "Subject updated successfully.",
        "data": subject.to_dict()
    }), 200

@subjects_bp.route('/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    """Delete a subject and all associated topics."""
    success, error, status_code = SubjectService.delete_subject(subject_id)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "message": f"Subject with ID {subject_id} and all related topics were deleted successfully."
    }), 200
