# Student Task Manager

A simple student task manager with user registration, login, task creation, completion tracking, and deletion.

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: SQLite

## Project Structure

```
student-task-manager/
│
├── backend/
│   ├── app.py
│   ├── database.db
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── README.md
└── .gitignore
```

## Setup

1. Open a terminal in the project root.
2. Create and activate a Python virtual environment:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

4. Run the Flask app:

```powershell
python backend\app.py
```

5. Open your browser at `http://127.0.0.1:5000`.

## Features

- Register a new user
- Login with username and password
- Add new tasks
- Mark tasks as completed or incomplete
- Delete tasks
- View your task list

## Notes

- The backend stores data in `backend/database.db`.
- The frontend is served by Flask so the API and UI run from the same origin.
