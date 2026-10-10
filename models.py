from datetime import datetime, timezone, date
from extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    weekday_hours = db.Column(db.Float, nullable=False, default=3.0)
    weekend_hours = db.Column(db.Float, nullable=False, default=6.0)
    exam_buffer_days = db.Column(db.Integer, nullable=False, default=2)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'weekday_hours': self.weekday_hours,
            'weekend_hours': self.weekend_hours,
            'exam_buffer_days': self.exam_buffer_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color_code = db.Column(db.String(20), nullable=False, default='#4F46E5')
    exam_date = db.Column(db.Date, nullable=False)
    difficulty_level = db.Column(db.Integer, nullable=False, default=3)  # 1 to 5
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    topics = db.relationship('Topic', backref='subject', cascade='all, delete-orphan', lazy=True)

    @property
    def days_until_exam(self):
        today = date.today()
        delta = (self.exam_date - today).days
        return max(0, delta)

    @property
    def completed_topic_count(self):
        return sum(1 for t in self.topics if t.status == 'completed')

    @property
    def progress_percentage(self):
        if not self.topics:
            return 0.0
        return round((self.completed_topic_count / len(self.topics)) * 100, 1)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color_code': self.color_code,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'difficulty_level': self.difficulty_level,
            'days_until_exam': self.days_until_exam,
            'topic_count': len(self.topics),
            'completed_topic_count': self.completed_topic_count,
            'progress_percentage': self.progress_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    estimated_hours = db.Column(db.Float, nullable=False, default=1.5)
    difficulty = db.Column(db.Integer, nullable=False, default=3)  # 1 to 5
    status = db.Column(db.String(20), nullable=False, default='not_started')  # 'not_started', 'in_progress', 'completed'
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    sessions = db.relationship('StudySession', backref='topic', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else None,
            'title': self.title,
            'estimated_hours': self.estimated_hours,
            'difficulty': self.difficulty,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudySession(db.Model):
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id', ondelete='CASCADE'), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    allocated_hours = db.Column(db.Float, nullable=False)
    is_revision = db.Column(db.Boolean, nullable=False, default=False)
    priority = db.Column(db.Float, nullable=False, default=1.0)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'completed', 'skipped'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    @property
    def session_type(self):
        return "revision" if self.is_revision else "learning"

    def to_dict(self):
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'topic_title': self.topic.title if self.topic else None,
            'subject_id': self.topic.subject_id if self.topic else None,
            'subject_name': self.topic.subject.name if self.topic and self.topic.subject else None,
            'color_code': self.topic.subject.color_code if self.topic and self.topic.subject else '#4F46E5',
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'allocated_hours': round(self.allocated_hours, 2),
            'session_type': self.session_type,
            'is_revision': self.is_revision,
            'priority': round(self.priority, 2),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

