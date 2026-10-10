import unittest
from datetime import date, timedelta
from app import create_app
from extensions import db
from models import Subject, Topic, UserSettings

class ApiCrudTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and an isolated in-memory testing database."""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Ensure default settings are initialized
        if not UserSettings.query.first():
            settings = UserSettings(weekday_hours=3.0, weekend_hours=6.0, exam_buffer_days=2)
            db.session.add(settings)
            db.session.commit()

    def tearDown(self):
        """Clean up database and pop context."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 1. Health Check
    def test_health_check(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['database'], 'connected')

    # 2. User Settings
    def test_get_settings(self):
        res = self.client.get('/api/settings')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['weekday_hours'], 3.0)
        self.assertEqual(data['data']['weekend_hours'], 6.0)

    def test_update_settings_valid(self):
        payload = {"weekday_hours": 4.5, "weekend_hours": 8.0, "exam_buffer_days": 3}
        res = self.client.put('/api/settings', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['weekday_hours'], 4.5)
        self.assertEqual(data['data']['weekend_hours'], 8.0)
        self.assertEqual(data['data']['exam_buffer_days'], 3)

    def test_update_settings_invalid(self):
        # Negative hours
        res = self.client.put('/api/settings', json={"weekday_hours": -2})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.get_json()['success'])

        # Hours > 24
        res = self.client.put('/api/settings', json={"weekend_hours": 30})
        self.assertEqual(res.status_code, 400)

        # Buffer days negative or invalid type
        res = self.client.put('/api/settings', json={"exam_buffer_days": -1})
        self.assertEqual(res.status_code, 400)

    # 3. Subjects CRUD
    def test_subject_crud_and_validation(self):
        # Empty subjects list
        res = self.client.get('/api/subjects')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['count'], 0)

        # Validation: Missing name
        future_date = (date.today() + timedelta(days=30)).isoformat()
        res = self.client.post('/api/subjects', json={"exam_date": future_date})
        self.assertEqual(res.status_code, 400)
        self.assertIn("name", res.get_json()['error'])

        # Validation: Invalid date format
        res = self.client.post('/api/subjects', json={"name": "Math", "exam_date": "not-a-date"})
        self.assertEqual(res.status_code, 400)

        # Validation: Difficulty out of bounds (1-5)
        res = self.client.post('/api/subjects', json={"name": "Math", "exam_date": future_date, "difficulty_level": 7})
        self.assertEqual(res.status_code, 400)

        # Valid Subject Creation
        payload = {
            "name": "Data Structures & Algorithms",
            "exam_date": future_date,
            "difficulty_level": 4,
            "color_code": "#6366F1"
        }
        res = self.client.post('/api/subjects', json=payload)
        self.assertEqual(res.status_code, 201)
        created = res.get_json()['data']
        self.assertEqual(created['name'], "Data Structures & Algorithms")
        self.assertEqual(created['difficulty_level'], 4)
        sub_id = created['id']

        # Get Single Subject
        res = self.client.get(f'/api/subjects/{sub_id}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['data']['id'], sub_id)
        self.assertIn('topics', res.get_json()['data'])

        # Update Subject (Valid)
        res = self.client.put(f'/api/subjects/{sub_id}', json={"name": "Advanced Algorithms", "difficulty_level": 5})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['data']['name'], "Advanced Algorithms")
        self.assertEqual(res.get_json()['data']['difficulty_level'], 5)

        # Update Subject (404 Non-existent)
        res = self.client.put('/api/subjects/9999', json={"name": "Ghost"})
        self.assertEqual(res.status_code, 404)

        # Get Subject (404 Non-existent)
        res = self.client.get('/api/subjects/9999')
        self.assertEqual(res.status_code, 404)

    # 4. Topics CRUD & Relationships
    def test_topics_crud_and_relationships(self):
        future_date = (date.today() + timedelta(days=20)).isoformat()
        sub_res = self.client.post('/api/subjects', json={
            "name": "Computer Networks",
            "exam_date": future_date,
            "difficulty_level": 3
        })
        sub_id = sub_res.get_json()['data']['id']

        # Validation: Topic with non-existent subject
        res = self.client.post('/api/topics', json={
            "subject_id": 8888,
            "title": "TCP/IP Protocol",
            "estimated_hours": 2.5
        })
        self.assertEqual(res.status_code, 404)

        # Validation: Missing title
        res = self.client.post('/api/topics', json={"subject_id": sub_id, "title": ""})
        self.assertEqual(res.status_code, 400)

        # Validation: Invalid difficulty
        res = self.client.post('/api/topics', json={"subject_id": sub_id, "title": "DNS", "difficulty": 0})
        self.assertEqual(res.status_code, 400)

        # Validation: Invalid status
        res = self.client.post('/api/topics', json={"subject_id": sub_id, "title": "DNS", "status": "finished"})
        self.assertEqual(res.status_code, 400)

        # Valid Topic Creation
        res = self.client.post('/api/topics', json={
            "subject_id": sub_id,
            "title": "OSI & TCP/IP Model",
            "estimated_hours": 3.0,
            "difficulty": 3,
            "status": "not_started"
        })
        self.assertEqual(res.status_code, 201)
        topic1 = res.get_json()['data']
        topic1_id = topic1['id']
        self.assertEqual(topic1['title'], "OSI & TCP/IP Model")
        self.assertIsNone(topic1['completed_at'])

        # Create Second Topic via convenience subject endpoint
        res2 = self.client.post(f'/api/subjects/{sub_id}/topics', json={
            "title": "Routing Algorithms",
            "estimated_hours": 4.0,
            "difficulty": 4
        })
        self.assertEqual(res2.status_code, 201)
        topic2_id = res2.get_json()['data']['id']

        # Get Topics For Subject
        res_list = self.client.get(f'/api/subjects/{sub_id}/topics')
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(res_list.get_json()['count'], 2)

        # Update Topic to completed
        res_update = self.client.patch(f'/api/topics/{topic1_id}', json={"status": "completed"})
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.get_json()['data']['status'], "completed")
        self.assertIsNotNone(res_update.get_json()['data']['completed_at'])

        # Check Subject progress calculation
        sub_check = self.client.get(f'/api/subjects/{sub_id}').get_json()['data']
        self.assertEqual(sub_check['topic_count'], 2)
        self.assertEqual(sub_check['completed_topic_count'], 1)
        self.assertEqual(sub_check['progress_percentage'], 50.0)

        # Delete Single Topic
        res_del = self.client.delete(f'/api/topics/{topic2_id}')
        self.assertEqual(res_del.status_code, 200)

        # Verify topic deletion
        res_404 = self.client.get(f'/api/topics/{topic2_id}')
        self.assertEqual(res_404.status_code, 404)

    # 5. Cascading Delete
    def test_cascading_delete(self):
        future_date = (date.today() + timedelta(days=15)).isoformat()
        sub_res = self.client.post('/api/subjects', json={
            "name": "Linear Algebra",
            "exam_date": future_date,
            "difficulty_level": 4
        })
        sub_id = sub_res.get_json()['data']['id']

        # Create two topics
        t1 = self.client.post('/api/topics', json={"subject_id": sub_id, "title": "Eigenvalues", "estimated_hours": 2.0}).get_json()['data']['id']
        t2 = self.client.post('/api/topics', json={"subject_id": sub_id, "title": "Vector Spaces", "estimated_hours": 3.0}).get_json()['data']['id']

        # Verify they exist
        self.assertEqual(self.client.get(f'/api/topics/{t1}').status_code, 200)
        self.assertEqual(self.client.get(f'/api/topics/{t2}').status_code, 200)

        # Delete Subject
        del_res = self.client.delete(f'/api/subjects/{sub_id}')
        self.assertEqual(del_res.status_code, 200)

        # Verify Subject is gone
        self.assertEqual(self.client.get(f'/api/subjects/{sub_id}').status_code, 404)

        # Verify Topics are cascade deleted
        self.assertEqual(self.client.get(f'/api/topics/{t1}').status_code, 404)
        self.assertEqual(self.client.get(f'/api/topics/{t2}').status_code, 404)

if __name__ == '__main__':
    unittest.main()
