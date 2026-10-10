import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')

    body = json.dumps(data).encode('utf-8') if data is not None else None
    try:
        with urllib.request.urlopen(req, data=body) as response:
            status = response.status
            resp_body = response.read().decode('utf-8')
            return status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        status = e.code
        resp_body = e.read().decode('utf-8')
        try:
            return status, json.loads(resp_body)
        except Exception:
            return status, {"raw": resp_body}
    except Exception as e:
        return 0, {"error": str(e)}

def assert_eq(actual, expected, msg):
    if actual != expected:
        print(f"[FAIL]: {msg} | Expected {expected}, got {actual}")
        sys.exit(1)
    else:
        print(f"[PASS]: {msg}")


def run_tests():
    print("--- Starting Live API Tests against http://127.0.0.1:5000 ---")

    # 1. Health check
    status, body = request("GET", "/api/health")
    assert_eq(status, 200, "Health check /api/health returns 200")
    assert_eq(body.get("database"), "connected", "Database connection is healthy")

    # 2. User Settings
    status, body = request("GET", "/api/settings")
    assert_eq(status, 200, "GET /api/settings returns 200")
    assert_eq(body.get("success"), True, "GET settings success is True")

    status, body = request("PUT", "/api/settings", {"weekday_hours": 4.0, "weekend_hours": 7.5, "exam_buffer_days": 3})
    assert_eq(status, 200, "PUT /api/settings valid update returns 200")
    assert_eq(body["data"]["weekday_hours"], 4.0, "Updated weekday_hours is 4.0")

    status, body = request("PUT", "/api/settings", {"weekday_hours": -5.0})
    assert_eq(status, 400, "PUT /api/settings negative hours returns 400")

    status, body = request("PUT", "/api/settings", {"exam_buffer_days": "not_an_int"})
    assert_eq(status, 400, "PUT /api/settings invalid buffer days returns 400")

    # 3. Subjects - Validation & 404
    status, body = request("GET", "/api/subjects/99999")
    assert_eq(status, 404, "GET non-existent subject returns 404")

    status, body = request("POST", "/api/subjects", {"exam_date": "2026-11-15"})
    assert_eq(status, 400, "POST subject without name returns 400")

    status, body = request("POST", "/api/subjects", {"name": "Physics", "exam_date": "invalid-date"})
    assert_eq(status, 400, "POST subject with invalid date returns 400")

    status, body = request("POST", "/api/subjects", {"name": "Physics", "exam_date": "2026-11-15", "difficulty_level": 9})
    assert_eq(status, 400, "POST subject with difficulty > 5 returns 400")

    # 3. Subjects - Create Valid
    status, body = request("POST", "/api/subjects", {
        "name": "Database Systems",
        "exam_date": "2026-11-20",
        "difficulty_level": 4,
        "color_code": "#3B82F6"
    })
    assert_eq(status, 201, "POST valid subject returns 201")
    subject_id = body["data"]["id"]
    assert_eq(body["data"]["name"], "Database Systems", "Subject name matches")

    # 3. Subjects - Get and Update
    status, body = request("GET", f"/api/subjects/{subject_id}")
    assert_eq(status, 200, "GET single subject returns 200")
    assert_eq(body["data"]["id"], subject_id, "Subject ID matches")

    status, body = request("PUT", f"/api/subjects/{subject_id}", {"name": "Advanced Database Systems", "difficulty_level": 5})
    assert_eq(status, 200, "PUT update subject returns 200")
    assert_eq(body["data"]["name"], "Advanced Database Systems", "Updated subject name matches")

    status, body = request("PUT", "/api/subjects/99999", {"name": "Nonexistent"})
    assert_eq(status, 404, "PUT non-existent subject returns 404")

    # 4. Topics - Validation & 404
    status, body = request("GET", "/api/topics/99999")
    assert_eq(status, 404, "GET non-existent topic returns 404")

    status, body = request("GET", "/api/subjects/99999/topics")
    assert_eq(status, 404, "GET topics for non-existent subject returns 404")

    status, body = request("POST", "/api/topics", {"subject_id": 99999, "title": "Indexing", "estimated_hours": 2})
    assert_eq(status, 404, "POST topic for non-existent subject returns 404")

    status, body = request("POST", "/api/topics", {"subject_id": subject_id, "title": "Indexing", "estimated_hours": -1})
    assert_eq(status, 400, "POST topic with negative hours returns 400")

    status, body = request("POST", "/api/topics", {"subject_id": subject_id, "title": "Indexing", "difficulty": 8})
    assert_eq(status, 400, "POST topic with difficulty > 5 returns 400")

    status, body = request("POST", "/api/topics", {"subject_id": subject_id, "title": "Indexing", "status": "unknown"})
    assert_eq(status, 400, "POST topic with invalid status returns 400")

    # 4. Topics - Create Valid
    status, body = request("POST", "/api/topics", {
        "subject_id": subject_id,
        "title": "B-Trees and Indexing",
        "estimated_hours": 3.0,
        "difficulty": 4,
        "status": "not_started"
    })
    assert_eq(status, 201, "POST valid topic returns 201")
    topic1_id = body["data"]["id"]

    # Create second topic via subject route
    status, body = request("POST", f"/api/subjects/{subject_id}/topics", {
        "title": "Query Optimization",
        "estimated_hours": 4.5,
        "difficulty": 5
    })
    assert_eq(status, 201, "POST topic via /api/subjects/<id>/topics returns 201")
    topic2_id = body["data"]["id"]

    # 4. Topics - List for Subject
    status, body = request("GET", f"/api/subjects/{subject_id}/topics")
    assert_eq(status, 200, "GET topics for subject returns 200")
    assert_eq(body["count"], 2, "Topic count for subject is 2")

    # 4. Topics - Update Status & Timestamps
    status, body = request("PATCH", f"/api/topics/{topic1_id}", {"status": "completed"})
    assert_eq(status, 200, "PATCH topic status returns 200")
    assert_eq(body["data"]["status"], "completed", "Topic status is now completed")
    assert_eq(body["data"]["completed_at"] is not None, True, "completed_at timestamp was set")

    # Check subject progress
    status, body = request("GET", f"/api/subjects/{subject_id}")
    assert_eq(body["data"]["completed_topic_count"], 1, "Completed topic count is 1")
    assert_eq(body["data"]["progress_percentage"], 50.0, "Progress percentage is 50.0%")

    # 4. Topics - Delete single topic
    status, body = request("DELETE", f"/api/topics/{topic2_id}")
    assert_eq(status, 200, "DELETE topic returns 200")
    status, body = request("GET", f"/api/topics/{topic2_id}")
    assert_eq(status, 404, "GET deleted topic returns 404")

    # 5. Cascading Delete Test
    # Create a fresh subject with 2 topics
    status, body = request("POST", "/api/subjects", {
        "name": "Cascade Test Subject",
        "exam_date": "2026-12-01",
        "difficulty_level": 3
    })
    cascade_sub_id = body["data"]["id"]
    status, body = request("POST", "/api/topics", {"subject_id": cascade_sub_id, "title": "Cascade Topic 1"})
    cascade_t1 = body["data"]["id"]
    status, body = request("POST", "/api/topics", {"subject_id": cascade_sub_id, "title": "Cascade Topic 2"})
    cascade_t2 = body["data"]["id"]

    # Verify topics exist
    status, _ = request("GET", f"/api/topics/{cascade_t1}")
    assert_eq(status, 200, "Cascade Topic 1 exists before subject delete")
    status, _ = request("GET", f"/api/topics/{cascade_t2}")
    assert_eq(status, 200, "Cascade Topic 2 exists before subject delete")

    # Delete Subject
    status, body = request("DELETE", f"/api/subjects/{cascade_sub_id}")
    assert_eq(status, 200, "DELETE subject returns 200")

    # Verify Subject is gone
    status, _ = request("GET", f"/api/subjects/{cascade_sub_id}")
    assert_eq(status, 404, "Subject is 404 after deletion")

    # Verify Topics are cascade-deleted
    status, _ = request("GET", f"/api/topics/{cascade_t1}")
    assert_eq(status, 404, "Cascade Topic 1 is 404 after subject deletion")
    status, _ = request("GET", f"/api/topics/{cascade_t2}")
    assert_eq(status, 404, "Cascade Topic 2 is 404 after subject deletion")

    # 6. Planner Endpoints Test
    # Generate study plan
    status, body = request("POST", "/api/plan/generate")
    assert_eq(status, 200, "POST /api/plan/generate returns 200")
    assert_eq(body.get("success"), True, "Plan generation success is True")
    assert_eq("summary" in body, True, "Plan generation response has summary")
    assert_eq(body["summary"]["total_sessions"] > 0, True, "Sessions were generated in plan")

    # Get plan
    status, body = request("GET", "/api/plan")
    assert_eq(status, 200, "GET /api/plan returns 200")
    assert_eq(body.get("success"), True, "GET /api/plan success is True")
    assert_eq(body["count"] > 0, True, "GET /api/plan returns scheduled sessions")

    # Verify session fields (date, topic, subject, planned hours, session type, priority)
    first_session = body["data"][0]
    assert_eq("scheduled_date" in first_session, True, "Session has scheduled_date")
    assert_eq("topic_title" in first_session, True, "Session has topic_title")
    assert_eq("subject_name" in first_session, True, "Session has subject_name")
    assert_eq("allocated_hours" in first_session, True, "Session has allocated_hours")
    assert_eq("session_type" in first_session, True, "Session has session_type")
    assert_eq("priority" in first_session, True, "Session has priority")

    # Rebalance plan
    status, body = request("POST", "/api/plan/rebalance")
    assert_eq(status, 200, "POST /api/plan/rebalance returns 200")
    assert_eq(body.get("success"), True, "POST /api/plan/rebalance success is True")

    # 7. Verify Health endpoint remains healthy
    status, body = request("GET", "/api/health")
    assert_eq(status, 200, "Final /api/health still returns 200")
    assert_eq(body["database"], "connected", "Database remains healthy and connected")

    print("\n[SUCCESS] ALL LIVE API TESTS PASSED SUCCESSFULLY! [SUCCESS]")



if __name__ == "__main__":
    run_tests()
