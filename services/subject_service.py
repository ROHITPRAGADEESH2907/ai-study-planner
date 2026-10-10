import re
from datetime import datetime, date
from extensions import db
from models import Subject

HEX_COLOR_REGEX = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')

class SubjectService:
    @staticmethod
    def get_all_subjects():
        """Retrieve all subjects ordered by upcoming exam date."""
        return Subject.query.order_by(Subject.exam_date.asc()).all()

    @staticmethod
    def get_subject_by_id(subject_id):
        """Retrieve a single subject by ID."""
        if not isinstance(subject_id, int):
            return None
        return db.session.get(Subject, subject_id)


    @staticmethod
    def create_subject(data):
        """
        Validate and create a new subject.
        Returns: (subject, error_message)
        """
        if not data or not isinstance(data, dict):
            return None, "Request body must be a valid JSON object."

        errors = []

        # Validate name
        name = data.get('name')
        if not name or not isinstance(name, str) or not name.strip():
            errors.append("Field 'name' is required and must be a non-empty string.")
        elif len(name.strip()) > 100:
            errors.append("Field 'name' must not exceed 100 characters.")

        # Validate exam_date
        exam_date_raw = data.get('exam_date')
        parsed_date = None
        if not exam_date_raw or not isinstance(exam_date_raw, str):
            errors.append("Field 'exam_date' is required and must be in 'YYYY-MM-DD' format.")
        else:
            try:
                parsed_date = datetime.strptime(exam_date_raw.strip(), '%Y-%m-%d').date()
            except ValueError:
                errors.append("Field 'exam_date' must be a valid date in 'YYYY-MM-DD' format.")

        # Validate difficulty_level
        difficulty = data.get('difficulty_level', 3)
        if isinstance(difficulty, bool) or not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
            errors.append("Field 'difficulty_level' must be an integer between 1 (easy) and 5 (hard).")

        # Validate color_code
        color_code = data.get('color_code', '#4F46E5')
        if not isinstance(color_code, str) or not HEX_COLOR_REGEX.match(color_code.strip()):
            errors.append("Field 'color_code' must be a valid hex color string (e.g., '#4F46E5').")

        if errors:
            return None, "; ".join(errors)

        try:
            subject = Subject(
                name=name.strip(),
                exam_date=parsed_date,
                difficulty_level=difficulty,
                color_code=color_code.strip()
            )
            db.session.add(subject)
            db.session.commit()
            return subject, None
        except Exception as e:
            db.session.rollback()
            return None, f"Database error creating subject: {str(e)}"

    @staticmethod
    def update_subject(subject_id, data):
        """
        Validate and update an existing subject.
        Returns: (subject, error_message, status_code)
        """
        subject = SubjectService.get_subject_by_id(subject_id)
        if not subject:
            return None, f"Subject with ID {subject_id} not found.", 404

        if not data or not isinstance(data, dict):
            return None, "Request body must be a valid JSON object.", 400

        errors = []

        if 'name' in data:
            name = data['name']
            if not isinstance(name, str) or not name.strip():
                errors.append("Field 'name' must be a non-empty string.")
            elif len(name.strip()) > 100:
                errors.append("Field 'name' must not exceed 100 characters.")
            else:
                subject.name = name.strip()

        if 'exam_date' in data:
            exam_date_raw = data['exam_date']
            if not isinstance(exam_date_raw, str):
                errors.append("Field 'exam_date' must be in 'YYYY-MM-DD' format.")
            else:
                try:
                    subject.exam_date = datetime.strptime(exam_date_raw.strip(), '%Y-%m-%d').date()
                except ValueError:
                    errors.append("Field 'exam_date' must be a valid date in 'YYYY-MM-DD' format.")

        if 'difficulty_level' in data:
            difficulty = data['difficulty_level']
            if isinstance(difficulty, bool) or not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
                errors.append("Field 'difficulty_level' must be an integer between 1 and 5.")
            else:
                subject.difficulty_level = difficulty

        if 'color_code' in data:
            color = data['color_code']
            if not isinstance(color, str) or not HEX_COLOR_REGEX.match(color.strip()):
                errors.append("Field 'color_code' must be a valid hex color string.")
            else:
                subject.color_code = color.strip()

        if errors:
            return None, "; ".join(errors), 400

        try:
            db.session.commit()
            return subject, None, 200
        except Exception as e:
            db.session.rollback()
            return None, f"Database error updating subject: {str(e)}", 500

    @staticmethod
    def delete_subject(subject_id):
        """
        Delete a subject and cascade delete all its associated topics.
        Returns: (success, error_message, status_code)
        """
        subject = SubjectService.get_subject_by_id(subject_id)
        if not subject:
            return False, f"Subject with ID {subject_id} not found.", 404

        try:
            db.session.delete(subject)
            db.session.commit()
            return True, None, 200
        except Exception as e:
            db.session.rollback()
            return False, f"Database error deleting subject: {str(e)}", 500
