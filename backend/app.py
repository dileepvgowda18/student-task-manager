import os
import sqlite3
from datetime import datetime
from flask import Flask, g, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        '''
    )
    conn.commit()
    conn.close()


init_db()


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username already exists.'}), 400

    user = conn.execute('SELECT id, username FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    session['user_id'] = user['id']
    return jsonify({'id': user['id'], 'username': user['username']})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user is None or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials.'}), 401

    session['user_id'] = user['id']
    return jsonify({'id': user['id'], 'username': user['username']})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'})


@app.route('/api/user', methods=['GET'])
def user_info():
    user = get_current_user()
    if not user:
        return jsonify({'user': None})
    return jsonify({'user': {'id': user['id'], 'username': user['username']}})


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required.'}), 401

    conn = get_db_connection()
    tasks = conn.execute(
        'SELECT id, title, description, completed, created_at FROM tasks WHERE user_id = ? ORDER BY created_at DESC',
        (user['id'],),
    ).fetchall()
    conn.close()
    task_list = [
        {
            'id': task['id'],
            'title': task['title'],
            'description': task['description'],
            'completed': bool(task['completed']),
            'created_at': task['created_at'],
        }
        for task in tasks
    ]
    return jsonify({'tasks': task_list})


@app.route('/api/tasks', methods=['POST'])
def create_task():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required.'}), 401

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title:
        return jsonify({'error': 'Task title is required.'}), 400

    created_at = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tasks (user_id, title, description, completed, created_at) VALUES (?, ?, ?, 0, ?)',
        (user['id'], title, description, created_at),
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return jsonify({
        'id': task_id,
        'title': title,
        'description': description,
        'completed': False,
        'created_at': created_at,
    }), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required.'}), 401

    data = request.get_json() or {}
    completed = data.get('completed')
    title = data.get('title')
    description = data.get('description')
    if completed is None and title is None and description is None:
        return jsonify({'error': 'Missing task fields.'}), 400

    conn = get_db_connection()
    task = conn.execute('SELECT id FROM tasks WHERE id = ? AND user_id = ?', (task_id, user['id'])).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found.'}), 404

    updates = []
    params = []
    if completed is not None:
        updates.append('completed = ?')
        params.append(1 if completed else 0)
    if title is not None:
        updates.append('title = ?')
        params.append(title.strip())
    if description is not None:
        updates.append('description = ?')
        params.append(description.strip())
    params.append(task_id)
    conn.execute(f'UPDATE tasks SET {", ".join(updates)} WHERE id = ?', tuple(params))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task updated.'})


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required.'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user['id']))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted == 0:
        return jsonify({'error': 'Task not found.'}), 404
    return jsonify({'message': 'Task deleted.'})


if __name__ == '__main__':
    app.run(debug=True)
