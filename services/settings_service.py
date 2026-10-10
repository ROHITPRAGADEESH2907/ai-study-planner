from extensions import db
from models import UserSettings

class SettingsService:
    @staticmethod
    def get_settings():
        """Retrieve existing user settings or create default if not found."""
        settings = UserSettings.query.first()
        if not settings:
            settings = UserSettings(
                weekday_hours=3.0,
                weekend_hours=6.0,
                exam_buffer_days=2
            )
            db.session.add(settings)
            db.session.commit()
        return settings

    @staticmethod
    def update_settings(data):
        """
        Validate and update user settings.
        Returns: (updated_settings, error_message)
        """
        if not data or not isinstance(data, dict):
            return None, "Request body must be a valid JSON object."

        settings = SettingsService.get_settings()
        errors = []

        if 'weekday_hours' in data:
            val = data['weekday_hours']
            if not isinstance(val, (int, float)) or val <= 0 or val > 24:
                errors.append("weekday_hours must be a number between 0.5 and 24.0.")
            else:
                settings.weekday_hours = float(val)

        if 'weekend_hours' in data:
            val = data['weekend_hours']
            if not isinstance(val, (int, float)) or val <= 0 or val > 24:
                errors.append("weekend_hours must be a number between 0.5 and 24.0.")
            else:
                settings.weekend_hours = float(val)

        if 'exam_buffer_days' in data:
            val = data['exam_buffer_days']
            if not isinstance(val, int) or isinstance(val, bool) or val < 0 or val > 30:
                errors.append("exam_buffer_days must be an integer between 0 and 30.")
            else:
                settings.exam_buffer_days = val

        if errors:
            return None, "; ".join(errors)

        try:
            db.session.commit()
            return settings, None
        except Exception as e:
            db.session.rollback()
            return None, f"Database error updating settings: {str(e)}"
