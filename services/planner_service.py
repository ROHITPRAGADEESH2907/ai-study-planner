from datetime import date, timedelta, datetime
from extensions import db
from models import Subject, Topic, StudySession, UserSettings
from services.settings_service import SettingsService

class PlannerService:
    """
    Deterministic Heuristic Study Planner Engine.
    Distributes uncompleted study topics across available days before exam deadlines
    using priority weighting, cognitive interleaving, capacity limits, and revision buffers.
    """

    @staticmethod
    def calculate_topic_priority(topic, subject, current_date):
        """
        Calculates priority score for a topic relative to an evaluation date.
        Formula:
            DaysLeft = max(1, (ExamDate - current_date).days)
            Priority = (TopicDifficulty * SubjectDifficulty * EstimatedHours) / DaysLeft
        Higher scores indicate greater urgency and effort requirements.
        """
        days_left = max(1, (subject.exam_date - current_date).days)
        base_priority = (topic.difficulty * subject.difficulty_level * topic.estimated_hours) / days_left
        return round(base_priority, 4)

    @classmethod
    def generate_plan(cls, start_date=None, clear_existing=True):
        """
        Generates study schedule sessions based on subjects, topics, and user settings.
        
        Args:
            start_date: date object or ISO string. Defaults to date.today().
            clear_existing: Boolean, whether to delete pending sessions from start_date onward.
            
        Returns:
            dict containing success status, summary, warnings, and created session dictionaries.
        """
        if start_date is None:
            eval_date = date.today()
        elif isinstance(start_date, str):
            try:
                eval_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return {"success": False, "error": "Invalid start_date format. Must be YYYY-MM-DD."}, 400
        else:
            eval_date = start_date

        settings = SettingsService.get_settings()
        buffer_days = settings.exam_buffer_days
        weekday_hours = settings.weekday_hours
        weekend_hours = settings.weekend_hours

        # Fetch subjects with future exam dates
        subjects = Subject.query.filter(Subject.exam_date > eval_date).all()
        if not subjects:
            if clear_existing:
                # Remove future pending sessions if no active subjects remain
                StudySession.query.filter(
                    StudySession.scheduled_date >= eval_date,
                    StudySession.status == 'pending'
                ).delete()
                db.session.commit()
            return {
                "success": True,
                "message": "No active upcoming subjects found with exams after the start date.",
                "summary": {
                    "total_sessions": 0,
                    "total_hours": 0.0,
                    "learning_sessions": 0,
                    "revision_sessions": 0,
                    "subjects_count": 0
                },
                "warnings": ["No upcoming subjects found with exam dates in the future."],
                "data": []
            }, 200

        # Fetch incomplete topics for these subjects
        subject_ids = [s.id for s in subjects]
        subject_map = {s.id: s for s in subjects}

        pending_topics = Topic.query.filter(
            Topic.subject_id.in_(subject_ids),
            Topic.status != 'completed'
        ).all()

        if not pending_topics:
            if clear_existing:
                StudySession.query.filter(
                    StudySession.scheduled_date >= eval_date,
                    StudySession.status == 'pending'
                ).delete()
                db.session.commit()
            return {
                "success": True,
                "message": "All topics are already marked as completed. No new sessions needed.",
                "summary": {
                    "total_sessions": 0,
                    "total_hours": 0.0,
                    "learning_sessions": 0,
                    "revision_sessions": 0,
                    "subjects_count": len(subjects)
                },
                "warnings": [],
                "data": []
            }, 200

        # Clear existing pending sessions from eval_date onward if requested
        if clear_existing:
            StudySession.query.filter(
                StudySession.scheduled_date >= eval_date,
                StudySession.status == 'pending'
            ).delete()
            db.session.commit()

        # Track remaining hours per topic for the heuristic schedule
        topic_workload = {}
        for t in pending_topics:
            topic_workload[t.id] = {
                'topic': t,
                'subject': subject_map[t.subject_id],
                'remaining_hours': float(t.estimated_hours)
            }

        # Calculate max simulation horizon (latest exam date)
        latest_exam = max(s.exam_date for s in subjects)
        total_days = (latest_exam - eval_date).days

        new_sessions = []
        last_scheduled_subject_id = None
        day_pointer = eval_date
        warnings = []

        total_hours_needed = sum(t.estimated_hours for t in pending_topics)
        total_hours_available = 0.0

        # Compute pre-exam buffer window for each subject
        # Buffer window: [exam_date - effective_buffer, exam_date - 1]
        subject_buffer_ranges = {}
        for s in subjects:
            days_until = (s.exam_date - eval_date).days
            effective_buffer = min(buffer_days, max(0, days_until // 2))
            buffer_start = s.exam_date - timedelta(days=effective_buffer)
            subject_buffer_ranges[s.id] = (buffer_start, s.exam_date)

        # Pre-cache topics list per subject to prevent autoflush overhead
        subject_topics = {s.id: list(s.topics) for s in subjects}

        # Simulation loop: day by day
        with db.session.no_autoflush:
            while day_pointer < latest_exam:
                is_weekend = day_pointer.weekday() in (5, 6)
                daily_limit = weekend_hours if is_weekend else weekday_hours
                total_hours_available += daily_limit
                allocated_today = 0.0

                # 1. Check if any subject is currently in its Revision Window on day_pointer
                # Give revision sessions priority during buffer days
                for s in subjects:
                    buf_start, exam_d = subject_buffer_ranges[s.id]
                    if buf_start <= day_pointer < exam_d:
                        # Subject is in buffer window! Allocate revision block if daily limit permits
                        remaining_cap = daily_limit - allocated_today
                        if remaining_cap >= 1.0:
                            # Find topic with highest difficulty under this subject for revision
                            # Filter out completed topics so revision only targets incomplete ones
                            candidate_rev_topics = [
                                t for t in subject_topics.get(s.id, [])
                                if t.status != 'completed'
                            ]
                            if candidate_rev_topics:
                                rev_topic = max(candidate_rev_topics, key=lambda x: (x.difficulty, x.estimated_hours))
                                rev_hours = min(1.5, remaining_cap)

                                # Ensure we don't duplicate multiple revision sessions on the exact same day for same subject
                                already_rev_today = any(
                                    sess.scheduled_date == day_pointer and sess.is_revision and
                                    (sess.topic.subject_id == s.id if sess.topic else False)
                                    for sess in new_sessions
                                )
                                if not already_rev_today:
                                    rev_session = StudySession(
                                        topic=rev_topic,
                                        topic_id=rev_topic.id,
                                        scheduled_date=day_pointer,
                                        allocated_hours=rev_hours,
                                        is_revision=True,
                                        priority=round(cls.calculate_topic_priority(rev_topic, s, day_pointer) * 1.5, 4),
                                        status='pending'
                                    )
                                    new_sessions.append(rev_session)
                                    allocated_today += rev_hours
                                    last_scheduled_subject_id = s.id

                # 2. Allocate Primary Learning Workload for available hours today
                while (daily_limit - allocated_today) >= 0.5:
                    # Find all eligible incomplete topics:
                    # - Must have remaining_hours > 0
                    # - Scheduled date must be before the subject's exam date
                    # - Scheduled date should preferably be before buffer window starts
                    eligible_entries = []
                    for tid, entry in topic_workload.items():
                        if entry['remaining_hours'] <= 0.01:
                            continue
                        subj = entry['subject']
                        # Hard rule: strictly before exam date
                        if day_pointer >= subj.exam_date:
                            continue
                        # Prefer scheduling before buffer window
                        buf_start, _ = subject_buffer_ranges[subj.id]
                        is_in_buffer = (day_pointer >= buf_start)
                        
                        priority = cls.calculate_topic_priority(entry['topic'], subj, day_pointer)
                        # Deprioritize learning sessions during buffer window if earlier days were available
                        if is_in_buffer:
                            priority *= 0.3

                        eligible_entries.append({
                            'tid': tid,
                            'topic': entry['topic'],
                            'subject': subj,
                            'remaining_hours': entry['remaining_hours'],
                            'priority': priority
                        })

                    if not eligible_entries:
                        # No more topics eligible or needing study on this day
                        break

                    # Interleaving heuristic:
                    # If multiple distinct subjects are available, prioritize topics from a DIFFERENT subject
                    # than the last scheduled subject to avoid cognitive fatigue.
                    distinct_subjects = set(e['subject'].id for e in eligible_entries)
                    candidates = eligible_entries

                    if len(distinct_subjects) > 1 and last_scheduled_subject_id is not None:
                        different_subj_candidates = [e for e in eligible_entries if e['subject'].id != last_scheduled_subject_id]
                        if different_subj_candidates:
                            candidates = different_subj_candidates

                    # Pick highest priority candidate
                    chosen = max(candidates, key=lambda x: x['priority'])
                    rem_capacity = daily_limit - allocated_today

                    # Determine session slice: between 0.5h and 2.0h
                    session_hours = min(chosen['remaining_hours'], 2.0, rem_capacity)
                    session_hours = round(session_hours, 2)

                    if session_hours < 0.25:
                        break

                    session = StudySession(
                        topic=chosen['topic'],
                        topic_id=chosen['topic'].id,
                        scheduled_date=day_pointer,
                        allocated_hours=session_hours,
                        is_revision=False,
                        priority=chosen['priority'],
                        status='pending'
                    )

                    new_sessions.append(session)
                    allocated_today += session_hours
                    topic_workload[chosen['tid']]['remaining_hours'] -= session_hours
                    last_scheduled_subject_id = chosen['subject'].id

                # Advance day
                day_pointer += timedelta(days=1)


        # Check if any topic could not fit before its exam date
        unfinished = [e for e in topic_workload.values() if e['remaining_hours'] > 0.05]
        if unfinished:
            unfinished_topics = ", ".join(f"{e['topic'].title} ({e['remaining_hours']:.1f}h left)" for e in unfinished[:3])
            warnings.append(
                f"Workload exceeded available daily study capacity. Could not fully schedule: {unfinished_topics}"
            )

        # Save all generated sessions to database
        try:
            db.session.add_all(new_sessions)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Database error saving plan: {str(e)}"}, 500

        # Construct response summary
        total_allocated = sum(s.allocated_hours for s in new_sessions)
        learning_count = sum(1 for s in new_sessions if not s.is_revision)
        revision_count = sum(1 for s in new_sessions if s.is_revision)

        return {
            "success": True,
            "message": f"Successfully generated study plan with {len(new_sessions)} sessions.",
            "summary": {
                "total_sessions": len(new_sessions),
                "total_hours": round(total_allocated, 2),
                "start_date": eval_date.isoformat(),
                "end_date": max((s.scheduled_date for s in new_sessions), default=eval_date).isoformat(),
                "learning_sessions": learning_count,
                "revision_sessions": revision_count,
                "subjects_count": len(subjects)
            },
            "warnings": warnings,
            "data": [s.to_dict() for s in new_sessions]
        }, 200

    @classmethod
    def get_plan(cls, start_date=None, end_date=None):
        """
        Retrieves generated study sessions within an optional date range.
        """
        query = StudySession.query

        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date() if isinstance(start_date, str) else start_date
                query = query.filter(StudySession.scheduled_date >= sd)
            except ValueError:
                return {"success": False, "error": "Invalid start_date format. Must be YYYY-MM-DD."}, 400

        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d').date() if isinstance(end_date, str) else end_date
                query = query.filter(StudySession.scheduled_date <= ed)
            except ValueError:
                return {"success": False, "error": "Invalid end_date format. Must be YYYY-MM-DD."}, 400

        sessions = query.order_by(StudySession.scheduled_date.asc(), StudySession.priority.desc()).all()

        total_hours = sum(s.allocated_hours for s in sessions)
        learning_count = sum(1 for s in sessions if not s.is_revision)
        revision_count = sum(1 for s in sessions if s.is_revision)

        return {
            "success": True,
            "count": len(sessions),
            "summary": {
                "total_hours": round(total_hours, 2),
                "learning_sessions": learning_count,
                "revision_sessions": revision_count
            },
            "data": [s.to_dict() for s in sessions]
        }, 200

    @classmethod
    def rebalance_plan(cls):
        """
        Rebalances the schedule from today onward:
        - Drops pending sessions for topics that have been completed.
        - Re-runs the deterministic planner engine to redistribute remaining work.
        """
        today = date.today()

        # 1. Delete pending sessions for topics that are completed
        completed_topic_ids = [t.id for t in Topic.query.filter_by(status='completed').all()]
        if completed_topic_ids:
            StudySession.query.filter(
                StudySession.topic_id.in_(completed_topic_ids),
                StudySession.status == 'pending'
            ).delete(synchronize_session=False)
            db.session.commit()

        # 2. Regenerate remaining pending schedule starting from today
        return cls.generate_plan(start_date=today, clear_existing=True)
