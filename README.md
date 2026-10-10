# 📚 AI Study Planner

> An intelligent, balanced study scheduling web application designed for college students to conquer exams without the last-minute cramming stress.

---

## 🎯 Project Overview

**AI Study Planner** helps college students convert complex course syllabi and exam deadlines into personalized, adaptive daily study plans. By factoring in exam dates, subject difficulty ratings, topic effort estimations, and daily study capacity, the application creates a realistic, interleaved study roadmap.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.13, Flask 3.x, Flask-SQLAlchemy 3.x
- **Database:** SQLite (persisted locally in `instance/study_planner.db`)
- **Frontend (Upcoming):** Semantic HTML5, Modern CSS (Glassmorphism & Flexbox/Grid), Vanilla JavaScript
- **Analytics (Upcoming):** Chart.js

---

## 🏗️ System Architecture

The project follows a **Modular Monolith** structure with clean separation of concerns:
- **Application Factory Pattern:** `create_app()` initializes config, extensions, and route blueprints.
- **Persistence Layer:** Flask-SQLAlchemy with SQLite models for `UserSettings`, `Subject`, `Topic`, and `StudySession`.
- **Service Layer:** Encapsulated heuristic planner engine, CRUD validation services, and analytics calculator.

---

## 📁 Project Structure

```
ai-study-planner/
├── .venv/                      # Python virtual environment
├── app.py                      # Application factory and entry point
├── config.py                   # Environment configs (development, testing, production)
├── extensions.py               # Shared extensions (SQLAlchemy instance)
├── models.py                   # Database schema and ORM models
├── routes/
│   ├── __init__.py             # Blueprints package initializer
│   ├── health.py               # Health-check endpoint (/api/health)
│   ├── planner.py              # Planner endpoints (/api/plan)
│   ├── settings.py             # User settings REST routes (/api/settings)
│   ├── subjects.py             # Subject CRUD routes (/api/subjects)
│   └── topics.py               # Topic CRUD routes (/api/topics)
├── services/
│   ├── __init__.py             # Services package initializer
│   ├── planner_service.py      # Heuristic planner engine & schedule generator
│   ├── settings_service.py     # Settings validation & update logic
│   ├── subject_service.py      # Subject validation & database operations
│   └── topic_service.py        # Topic validation & database operations
├── tests/
│   ├── __init__.py             # Tests package initializer
│   ├── test_api.py             # In-memory unit test suite (CRUD & settings)
│   ├── test_planner.py         # Planner engine unit tests (priority, buffer, interleaving)
│   └── verify_live_api.py      # Live HTTP end-to-end integration test suite
├── instance/
│   └── study_planner.db        # SQLite database file (auto-generated)
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git exclusions for Python & SQLite
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- `pip` package manager

### 2. Environment Setup

Clone or open the repository directory:
```bash
cd "C:\Users\RohitPragadeesh JB\.gemini\antigravity\scratch\ai-study-planner"
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database & Run
```bash
python app.py
```
The server will start at `http://127.0.0.1:5000`. The SQLite database and tables will be created automatically in `instance/study_planner.db`.

### 4. Health-Check Verification
Verify the server status and database connectivity:
```bash
curl http://127.0.0.1:5000/api/health
```
Expected response:
```json
{
  "status": "ok",
  "service": "AI Study Planner API",
  "database": "connected"
}
```

---

## 📊 Database Models

1. **`UserSettings` (`user_settings`)**: Stores default weekday and weekend available study hours and exam buffer window.
2. **`Subject` (`subjects`)**: Stores course name, color code, exam date, difficulty level (1–5), and countdown properties.
3. **`Topic` (`topics`)**: Granular syllabus items with estimated completion hours, difficulty, and completion status.
4. **`StudySession` (`study_sessions`)**: Concrete daily study assignments scheduled by the planning algorithm.

---

## 📡 REST API Reference

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/api/health` | Service health & database connectivity check | `200` |
| `GET` | `/api/settings` | Retrieve user study settings | `200` |
| `PUT` | `/api/settings` | Update user study settings | `200` / `400` |
| `GET` | `/api/subjects` | List all subjects ordered by exam date | `200` |
| `GET` | `/api/subjects/<id>` | Get single subject with nested topics list | `200` / `404` |
| `POST` | `/api/subjects` | Create a new subject | `201` / `400` |
| `PUT` | `/api/subjects/<id>` | Update an existing subject | `200` / `400` / `404` |
| `DELETE` | `/api/subjects/<id>` | Delete subject (cascades to all its topics) | `200` / `404` |
| `GET` | `/api/subjects/<id>/topics`| List all topics belonging to a subject | `200` / `404` |
| `POST` | `/api/subjects/<id>/topics`| Convenience route to add topic to subject | `201` / `400` / `404` |
| `GET` | `/api/topics/<id>` | Retrieve a single topic by ID | `200` / `404` |
| `POST` | `/api/topics` | Create a new topic specifying `subject_id` | `201` / `400` / `404` |
| `PUT` / `PATCH` | `/api/topics/<id>` | Update topic details or toggle completion | `200` / `400` / `404` |
| `DELETE` | `/api/topics/<id>` | Delete a topic | `200` / `404` |
| `POST` | `/api/plan/generate` | Generate study plan from current subjects/topics | `200` / `400` / `500` |
| `GET` | `/api/plan` | Retrieve scheduled sessions (optional date filters) | `200` / `400` |
| `POST` | `/api/plan/rebalance` | Recalibrate schedule based on completed progress | `200` / `500` |

---

## 🧠 Planner Heuristic Engine

The planner uses a **deterministic, priority-weighted scheduling algorithm** (no external AI API) that:

1. **Prioritizes** topics using the formula: `Priority = (TopicDifficulty × SubjectDifficulty × EstimatedHours) / DaysUntilExam`. Closer exams, harder topics, and larger workloads score higher.
2. **Respects daily capacity** — allocates up to `weekday_hours` on weekdays and `weekend_hours` on weekends.
3. **Reserves exam-buffer days** for revision sessions before each exam. Revision topics are selected by difficulty and receive a 1.5× priority boost.
4. **Interleaves subjects** — when multiple subjects are available, it alternates between them to reduce cognitive fatigue.
5. **Excludes completed topics** from both learning and revision scheduling.
6. **Rebalancing** drops sessions for newly completed topics and regenerates the remaining schedule from today onward.

---

## 🗺️ Roadmap

- [x] **Phase 1: Foundation & Data Layer** — Flask app factory, SQLite database schema, configuration, models, and health-check endpoint.
- [x] **Phase 2: Core CRUD REST API** — Blueprints, services layer, payload validations, cascading deletes, and end-to-end tests.
- [x] **Phase 3: Planner Heuristic Engine** — Priority-weighted distribution algorithm with interleaved practice.
- [x] **Phase 4: Modern Frontend UI** — Responsive dashboard, subjects manager, topics manager, study timetable, and settings.
- [x] **Phase 5: Timetable & Progress Visualizations** — Visual calendar timetable, progress bars, and readiness metrics.
- [x] **Phase 6: Dynamic Rebalancing & Polish** — One-click plan recalibration, responsive UX, and portfolio-ready styling.

