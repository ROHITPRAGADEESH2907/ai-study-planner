from datetime import datetime, timezone
from extensions import db
from models import Topic, Subject

VALID_STATUSES = {'not_started', 'in_progress', 'completed'}

class TopicService:
    @staticmethod
    def get_topics_for_subject(subject_id):
        """Retrieve all topics belonging to a specific subject."""
        if not isinstance(subject_id, int):
            return None, "Invalid subject ID.", 400

        subject = db.session.get(Subject, subject_id)
        if not subject:
            return None, f"Subject with ID {subject_id} not found.", 404

        topics = Topic.query.filter_by(subject_id=subject_id).order_by(Topic.id.asc()).all()
        return topics, None, 200

    @staticmethod
    def get_topic_by_id(topic_id):
        """Retrieve a single topic by ID."""
        if not isinstance(topic_id, int):
            return None, "Invalid topic ID.", 400

        topic = db.session.get(Topic, topic_id)
        if not topic:
            return None, f"Topic with ID {topic_id} not found.", 404
        return topic, None, 200

    @staticmethod
    def create_topic(data):
        """
        Validate and create a new topic under a subject.
        Returns: (topic, error_message, status_code)
        """
        if not data or not isinstance(data, dict):
            return None, "Request body must be a valid JSON object.", 400

        errors = []

        # Validate subject_id
        subject_id = data.get('subject_id')
        if subject_id is None or isinstance(subject_id, bool) or not isinstance(subject_id, int):
            errors.append("Field 'subject_id' is required and must be an integer.")
        else:
            subject = db.session.get(Subject, subject_id)
            if not subject:
                return None, f"Subject with ID {subject_id} does not exist.", 404

        # Validate title
        title = data.get('title')
        if not title or not isinstance(title, str) or not title.strip():
            errors.append("Field 'title' is required and must be a non-empty string.")
        elif len(title.strip()) > 150:
            errors.append("Field 'title' must not exceed 150 characters.")

        # Validate estimated_hours
        estimated_hours = data.get('estimated_hours', 1.5)
        if not isinstance(estimated_hours, (int, float)) or estimated_hours <= 0 or estimated_hours > 50:
            errors.append("Field 'estimated_hours' must be a positive number up to 50.0.")

        # Validate difficulty
        difficulty = data.get('difficulty', 3)
        if isinstance(difficulty, bool) or not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
            errors.append("Field 'difficulty' must be an integer between 1 and 5.")

        # Validate status
        status = data.get('status', 'not_started')
        if not isinstance(status, str) or status.lower().strip() not in VALID_STATUSES:
            errors.append(f"Field 'status' must be one of: {', '.join(sorted(VALID_STATUSES))}.")
        else:
            status = status.lower().strip()

        if errors:
            return None, "; ".join(errors), 400

        completed_at = datetime.now(timezone.utc) if status == 'completed' else None

        try:
            topic = Topic(
                subject_id=subject_id,
                title=title.strip(),
                estimated_hours=float(estimated_hours),
                difficulty=difficulty,
                status=status,
                completed_at=completed_at
            )
            db.session.add(topic)
            db.session.commit()
            return topic, None, 201
        except Exception as e:
            db.session.rollback()
            return None, f"Database error creating topic: {str(e)}", 500

    @staticmethod
    def update_topic(topic_id, data):
        """
        Validate and update an existing topic.
        Returns: (topic, error_message, status_code)
        """
        topic = db.session.get(Topic, topic_id)
        if not topic:
            return None, f"Topic with ID {topic_id} not found.", 404

        if not data or not isinstance(data, dict):
            return None, "Request body must be a valid JSON object.", 400

        errors = []

        if 'subject_id' in data:
            new_subject_id = data['subject_id']
            if isinstance(new_subject_id, bool) or not isinstance(new_subject_id, int):
                errors.append("Field 'subject_id' must be an integer.")
            else:
                target_subject = db.session.get(Subject, new_subject_id)
                if not target_subject:
                    return None, f"Target subject with ID {new_subject_id} does not exist.", 404
                topic.subject_id = new_subject_id

        if 'title' in data:
            title = data['title']
            if not isinstance(title, str) or not title.strip():
                errors.append("Field 'title' must be a non-empty string.")
            elif len(title.strip()) > 150:
                errors.append("Field 'title' must not exceed 150 characters.")
            else:
                topic.title = title.strip()

        if 'estimated_hours' in data:
            estimated_hours = data['estimated_hours']
            if not isinstance(estimated_hours, (int, float)) or estimated_hours <= 0 or estimated_hours > 50:
                errors.append("Field 'estimated_hours' must be a positive number up to 50.0.")
            else:
                topic.estimated_hours = float(estimated_hours)

        if 'difficulty' in data:
            difficulty = data['difficulty']
            if isinstance(difficulty, bool) or not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
                errors.append("Field 'difficulty' must be an integer between 1 and 5.")
            else:
                topic.difficulty = difficulty

        if 'status' in data:
            status = data['status']
            if not isinstance(status, str) or status.lower().strip() not in VALID_STATUSES:
                errors.append(f"Field 'status' must be one of: {', '.join(sorted(VALID_STATUSES))}.")
            else:
                normalized_status = status.lower().strip()
                if normalized_status == 'completed' and topic.status != 'completed':
                    topic.completed_at = datetime.now(timezone.utc)
                elif normalized_status != 'completed' and topic.status == 'completed':
                    topic.completed_at = None
                topic.status = normalized_status

        if errors:
            return None, "; ".join(errors), 400

        try:
            db.session.commit()
            return topic, None, 200
        except Exception as e:
            db.session.rollback()
            return None, f"Database error updating topic: {str(e)}", 500

    @staticmethod
    def delete_topic(topic_id):
        """
        Delete a topic and cascade delete all its study sessions.
        Returns: (success, error_message, status_code)
        """
        topic = db.session.get(Topic, topic_id)
        if not topic:
            return False, f"Topic with ID {topic_id} not found.", 404

        try:
            db.session.delete(topic)
            db.session.commit()
            return True, None, 200
        except Exception as e:
            db.session.rollback()
            return False, f"Database error deleting topic: {str(e)}", 500
