# TaskFlow — Flask + SQLite Web App

A minimal one-page task manager built with Python Flask and SQLite.

## Project Structure
```
taskapp/
├── app.py               # Flask backend + database models + routes
├── requirements.txt     # Python dependencies
└── templates/
    └── index.html       # Single-page frontend
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
http://localhost:5000
```

## Features
- Add tasks
- Mark tasks as complete / incomplete
- Delete tasks
- SQLite database (tasks.db created automatically on first run)
- REST API endpoints for testing:
  - GET  /api/tasks        → list all tasks
  - POST /api/tasks        → create task (JSON body: {"title": "..."})

## Routes
| Method | Route                  | Description          |
|--------|------------------------|----------------------|
| GET    | /                      | Home page            |
| POST   | /add                   | Add a new task       |
| POST   | /toggle/<id>           | Toggle done/undone   |
| POST   | /delete/<id>           | Delete a task        |
| GET    | /api/tasks             | JSON list of tasks   |
| POST   | /api/tasks             | Create task via API  |
