# 📚 AI Study Planner

An intelligent study scheduling web application that helps college students organize subjects, track syllabus progress, plan study sessions, and prepare for exams without last-minute cramming.

## 🎯 Project Overview

AI Study Planner converts subjects, topics, exam dates, difficulty levels, and available study time into a structured study plan. It helps students prioritize important topics, monitor progress, and rebalance their schedules when plans change.

## ✨ Features

- **Dashboard:** View study progress, upcoming exams, and today's study sessions.
- **Subject Management:** Add, view, update, and manage academic subjects.
- **Topic Management:** Organize syllabus topics and track their completion status.
- **Study Planner:** Generate a study schedule based on study preferences and topic requirements.
- **Schedule Rebalancing:** Rebalance study sessions when your schedule changes.
- **Analytics:** Review study progress and readiness metrics.
- **Settings:** Configure study preferences and daily study capacity.
- **REST API:** Flask endpoints for subjects, topics, settings, and study planning.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **ORM:** Flask-SQLAlchemy
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Testing:** Python unittest

## 🏗️ Architecture

The application follows a modular monolith architecture with a clear separation of responsibilities:

- **Routes:** Handle HTTP requests and API endpoints.
- **Models:** Define database entities and relationships.
- **Services:** Implement subject, topic, settings, and planning logic.
- **Templates:** Render the web application's pages.
- **Static Assets:** Store CSS and JavaScript files.
- **Tests:** Verify API behavior and study-planning functionality.

## 📂 Project Structure

```text
ai-study-planner/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── requirements.txt
├── README.md
├── routes/
├── services/
├── templates/
├── static/
│   ├── css/
│   └── js/
├── tests/
└── instance/
```

The SQLite database and local environment files are excluded from version control.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or newer
- pip

### 1. Clone the repository

```bash
git clone https://github.com/ROHITPRAGADEESH2907/ai-study-planner.git
cd ai-study-planner
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open the local address displayed in your terminal, typically:

`http://127.0.0.1:5000`

## 🧪 Running Tests

Run the project's test suite with:

```bash
python -m unittest discover -s tests
```

## 🔒 Data and Configuration

The application uses SQLite for local persistence. Database files, virtual environments, and environment configuration files should remain untracked by Git.

## 🔮 Future Improvements

- User authentication and individual student profiles
- Calendar integration and reminders
- Exportable study schedules
- Enhanced progress visualization
- Optional AI-assisted study recommendations

## 👨‍💻 Author

**Rohit Pragadeesh J.B.**

GitHub: [@ROHITPRAGADEESH2907](https://github.com/ROHITPRAGADEESH2907)

---

*Built to make exam preparation more organized, balanced, and productive.*
