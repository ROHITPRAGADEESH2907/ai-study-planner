import unittest
from datetime import date, timedelta
from app import create_app
from extensions import db
from models import Subject, Topic, StudySession, UserSettings
from services.planner_service import PlannerService

class PlannerEngineTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated testing app and database."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Initialize base settings: 3h weekdays, 6h weekends, 2 buffer days
        settings = UserSettings(weekday_hours=3.0, weekend_hours=6.0, exam_buffer_days=2)
        db.session.add(settings)
        db.session.commit()

        self.today = date.today()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 1. Test: No subjects/topics
    def test_no_subjects_or_topics(self):
        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['total_sessions'], 0)
        self.assertEqual(len(data['data']), 0)

    # 2. Test: One subject with multiple topics
    def test_one_subject_multiple_topics(self):
        exam_date = self.today + timedelta(days=7)
        s = Subject(name="Operating Systems", exam_date=exam_date, difficulty_level=3)
        db.session.add(s)
        db.session.commit()

        t1 = Topic(subject_id=s.id, title="Processes & Threads", estimated_hours=2.0, difficulty=3)
        t2 = Topic(subject_id=s.id, title="Memory Management", estimated_hours=3.0, difficulty=4)
        db.session.add_all([t1, t2])
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['summary']['total_sessions'], 0)

        # Check all sessions are before exam date
        for session in data['data']:
            sess_date = date.fromisoformat(session['scheduled_date'])
            self.assertLess(sess_date, exam_date, "Session scheduled on or after exam date!")

    # 3. Test: Multiple subjects with different exam dates (urgency priority)
    def test_multiple_subjects_different_exam_dates(self):
        near_exam = self.today + timedelta(days=4)
        far_exam = self.today + timedelta(days=20)

        s_near = Subject(name="Near Subject", exam_date=near_exam, difficulty_level=3)
        s_far = Subject(name="Far Subject", exam_date=far_exam, difficulty_level=3)
        db.session.add_all([s_near, s_far])
        db.session.commit()

        t_near = Topic(subject_id=s_near.id, title="Near Topic", estimated_hours=2.0, difficulty=3)
        t_far = Topic(subject_id=s_far.id, title="Far Topic", estimated_hours=2.0, difficulty=3)
        db.session.add_all([t_near, t_far])
        db.session.commit()

        p_near = PlannerService.calculate_topic_priority(t_near, s_near, self.today)
        p_far = PlannerService.calculate_topic_priority(t_far, s_far, self.today)

        # Near exam must have substantially higher priority score
        self.assertGreater(p_near, p_far, "Closer exam did not receive higher priority score!")

    # 4. Test: Different topic difficulties
    def test_different_topic_difficulties(self):
        exam_date = self.today + timedelta(days=10)
        s = Subject(name="Algorithms", exam_date=exam_date, difficulty_level=4)
        db.session.add(s)
        db.session.commit()

        easy_topic = Topic(subject_id=s.id, title="Array Traversal", estimated_hours=2.0, difficulty=1)
        hard_topic = Topic(subject_id=s.id, title="Dynamic Programming", estimated_hours=2.0, difficulty=5)
        db.session.add_all([easy_topic, hard_topic])
        db.session.commit()

        p_easy = PlannerService.calculate_topic_priority(easy_topic, s, self.today)
        p_hard = PlannerService.calculate_topic_priority(hard_topic, s, self.today)

        self.assertGreater(p_hard, p_easy, "Harder topic did not receive higher priority score!")

    # 5 & 13. Test: Completed topics are not scheduled
    def test_completed_topics_not_scheduled(self):
        exam_date = self.today + timedelta(days=8)
        s = Subject(name="Software Engineering", exam_date=exam_date, difficulty_level=3)
        db.session.add(s)
        db.session.commit()

        t_done = Topic(subject_id=s.id, title="Agile Basics", estimated_hours=2.0, difficulty=2, status="completed")
        t_pending = Topic(subject_id=s.id, title="Design Patterns", estimated_hours=3.0, difficulty=4, status="not_started")
        db.session.add_all([t_done, t_pending])
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        sessions = res.get_json()['data']

        topic_titles = [sess['topic_title'] for sess in sessions]
        self.assertNotIn("Agile Basics", topic_titles, "Completed topic was scheduled!")
        self.assertIn("Design Patterns", topic_titles)

    # 6 & 11. Test: Limited daily study hours and no daily capacity exceeded
    def test_daily_capacity_constraints(self):
        # Configure strictly limited daily hours: 2.0h weekday, 2.0h weekend
        settings = UserSettings.query.first()
        settings.weekday_hours = 2.0
        settings.weekend_hours = 2.0
        db.session.commit()

        exam_date = self.today + timedelta(days=10)
        s = Subject(name="Calculus", exam_date=exam_date, difficulty_level=4)
        db.session.add(s)
        db.session.commit()

        # 6 hours of work total
        t = Topic(subject_id=s.id, title="Differential Equations", estimated_hours=6.0, difficulty=4)
        db.session.add(t)
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        sessions = res.get_json()['data']

        # Group by date and check total hours per day
        daily_hours = {}
        for sess in sessions:
            d = sess['scheduled_date']
            daily_hours[d] = daily_hours.get(d, 0.0) + sess['allocated_hours']

        for d, total_h in daily_hours.items():
            self.assertLessEqual(round(total_h, 2), 2.0, f"Daily capacity exceeded on {d}: {total_h}h > 2.0h")

    # 7. Test: Weekend capacity differences
    def test_weekend_capacity(self):
        settings = UserSettings.query.first()
        settings.weekday_hours = 1.0
        settings.weekend_hours = 5.0
        db.session.commit()

        exam_date = self.today + timedelta(days=14)
        s = Subject(name="Statistics", exam_date=exam_date, difficulty_level=3)
        db.session.add(s)
        db.session.commit()

        t = Topic(subject_id=s.id, title="Probability Distributions", estimated_hours=10.0, difficulty=3)
        db.session.add(t)
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        sessions = res.get_json()['data']

        daily_hours = {}
        for sess in sessions:
            d = sess['scheduled_date']
            daily_hours[d] = daily_hours.get(d, 0.0) + sess['allocated_hours']

        for d_str, hours in daily_hours.items():
            d_obj = date.fromisoformat(d_str)
            is_weekend = d_obj.weekday() in (5, 6)
            limit = 5.0 if is_weekend else 1.0
            self.assertLessEqual(round(hours, 2), limit + 0.01, f"Limit exceeded on {d_str}")

    # 8. Test: Exam-buffer days contains revision sessions
    def test_exam_buffer_revision_sessions(self):
        exam_date = self.today + timedelta(days=6)
        s = Subject(name="Compilers", exam_date=exam_date, difficulty_level=4)
        db.session.add(s)
        db.session.commit()

        t1 = Topic(subject_id=s.id, title="Lexical Analysis", estimated_hours=2.0, difficulty=3)
        t2 = Topic(subject_id=s.id, title="Syntax Parsing", estimated_hours=3.0, difficulty=5)
        db.session.add_all([t1, t2])
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        sessions = res.get_json()['data']

        revision_sessions = [sess for sess in sessions if sess['is_revision']]
        self.assertGreater(len(revision_sessions), 0, "No revision sessions scheduled in buffer window!")
        self.assertEqual(revision_sessions[0]['session_type'], 'revision')

    # 9. Test: Multiple subjects being interleaved
    def test_interleaving_subjects(self):
        exam_date = self.today + timedelta(days=12)
        s1 = Subject(name="Subject Alpha", exam_date=exam_date, difficulty_level=3)
        s2 = Subject(name="Subject Beta", exam_date=exam_date, difficulty_level=3)
        db.session.add_all([s1, s2])
        db.session.commit()

        # Two 3-hour topics for each subject
        t1a = Topic(subject_id=s1.id, title="Alpha Topic 1", estimated_hours=3.0, difficulty=3)
        t1b = Topic(subject_id=s1.id, title="Alpha Topic 2", estimated_hours=3.0, difficulty=3)
        t2a = Topic(subject_id=s2.id, title="Beta Topic 1", estimated_hours=3.0, difficulty=3)
        t2b = Topic(subject_id=s2.id, title="Beta Topic 2", estimated_hours=3.0, difficulty=3)
        db.session.add_all([t1a, t1b, t2a, t2b])
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        sessions = res.get_json()['data']

        # Check subject alternation among learning sessions
        learning_sessions = [s for s in sessions if not s['is_revision']]
        self.assertGreater(len(learning_sessions), 3)

        # Confirm that both subjects appear early in the schedule (interleaved, not blocked)
        first_three_subjects = set(s['subject_name'] for s in learning_sessions[:3])
        self.assertEqual(len(first_three_subjects), 2, "Sessions were not interleaved across subjects!")

    # 10. Test: Rebalancing after a topic is completed
    def test_rebalancing_after_topic_completion(self):
        exam_date = self.today + timedelta(days=10)
        s = Subject(name="Database", exam_date=exam_date, difficulty_level=3)
        db.session.add(s)
        db.session.commit()

        t1 = Topic(subject_id=s.id, title="Normalization", estimated_hours=3.0, difficulty=3)
        t2 = Topic(subject_id=s.id, title="Transactions", estimated_hours=3.0, difficulty=4)
        db.session.add_all([t1, t2])
        db.session.commit()

        # Initial plan
        self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})

        # Mark t1 as completed
        t1.status = 'completed'
        db.session.commit()

        # Call rebalance
        reb_res = self.client.post('/api/plan/rebalance')
        self.assertEqual(reb_res.status_code, 200)
        reb_sessions = reb_res.get_json()['data']

        # Verify t1 is no longer in any learning session
        learning_titles = [sess['topic_title'] for sess in reb_sessions if not sess['is_revision']]
        self.assertNotIn("Normalization", learning_titles, "Completed topic still found in learning sessions after rebalance!")
        self.assertIn("Transactions", learning_titles)

    # 12. Test: No sessions created on or after exam date
    def test_no_sessions_after_exam_date(self):
        exam_date = self.today + timedelta(days=5)
        s = Subject(name="Ethics", exam_date=exam_date, difficulty_level=2)
        db.session.add(s)
        db.session.commit()

        t = Topic(subject_id=s.id, title="Case Studies", estimated_hours=8.0, difficulty=2)
        db.session.add(t)
        db.session.commit()

        res = self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})
        self.assertEqual(res.status_code, 200)
        sessions = res.get_json()['data']

        for sess in sessions:
            sess_date = date.fromisoformat(sess['scheduled_date'])
            self.assertLess(sess_date, exam_date, f"Session date {sess_date} is on or after exam {exam_date}!")

    # API Plan Retrieval Tests
    def test_get_plan_endpoint(self):
        exam_date = self.today + timedelta(days=8)
        s = Subject(name="AI Intro", exam_date=exam_date, difficulty_level=3)
        db.session.add(s)
        db.session.commit()
        t = Topic(subject_id=s.id, title="Search Algorithms", estimated_hours=2.0, difficulty=3)
        db.session.add(t)
        db.session.commit()

        self.client.post('/api/plan/generate', json={"start_date": self.today.isoformat()})

        # Test GET /api/plan
        res = self.client.get('/api/plan')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['count'], 0)
        self.assertIn('summary', data)
        self.assertIn('total_hours', data['summary'])

if __name__ == '__main__':
    unittest.main()
