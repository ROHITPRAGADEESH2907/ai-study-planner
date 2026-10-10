from flask import Blueprint, request, jsonify
from services.topic_service import TopicService

topics_bp = Blueprint('topics', __name__)

@topics_bp.route('/api/subjects/<int:subject_id>/topics', methods=['GET'])
def get_subject_topics(subject_id):
    """Retrieve all topics under a specific subject."""
    topics, error, status_code = TopicService.get_topics_for_subject(subject_id)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "count": len(topics),
        "data": [t.to_dict() for t in topics]
    }), 200

@topics_bp.route('/api/subjects/<int:subject_id>/topics', methods=['POST'])
def create_topic_under_subject(subject_id):
    """Helper route to create a topic directly under a subject path."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON or empty body."
        }), 400

    data_copy = dict(data)
    data_copy['subject_id'] = subject_id

    topic, error, status_code = TopicService.create_topic(data_copy)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "message": "Topic created successfully.",
        "data": topic.to_dict()
    }), status_code

@topics_bp.route('/api/topics/<int:topic_id>', methods=['GET'])
def get_topic(topic_id):
    """Retrieve a single topic by ID."""
    topic, error, status_code = TopicService.get_topic_by_id(topic_id)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "data": topic.to_dict()
    }), 200

@topics_bp.route('/api/topics', methods=['POST'])
def create_topic():
    """Create a new topic specifying subject_id in JSON payload."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON or empty body."
        }), 400

    topic, error, status_code = TopicService.create_topic(data)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "message": "Topic created successfully.",
        "data": topic.to_dict()
    }), status_code

@topics_bp.route('/api/topics/<int:topic_id>', methods=['PUT', 'PATCH'])
def update_topic(topic_id):
    """Update an existing topic."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON or empty body."
        }), 400

    topic, error, status_code = TopicService.update_topic(topic_id, data)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "message": "Topic updated successfully.",
        "data": topic.to_dict()
    }), 200

@topics_bp.route('/api/topics/<int:topic_id>', methods=['DELETE'])
def delete_topic(topic_id):
    """Delete a topic and its study sessions."""
    success, error, status_code = TopicService.delete_topic(topic_id)
    if error:
        return jsonify({
            "success": False,
            "error": error
        }), status_code

    return jsonify({
        "success": True,
        "message": f"Topic with ID {topic_id} was deleted successfully."
    }), 200
