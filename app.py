import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request
 
app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "tasks.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
 
 
def db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection
 
 
def initialize_db():
    connection = db_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
    finally:
        connection.close()

@app.get("/")
def index():
    return jsonify({
        "service": os.getenv("APP_NAME", "Cloud Tasks"),
        "status": "running"
    })
 
 
@app.get("/health")
def health():
    return jsonify({"status": "ok"})
 
 
@app.get("/api/tasks")
def list_tasks():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400
    
    done = data.get("done")
    if type(done) is not bool:
        return jsonify({"error": "Ожидается bool(true or false)"}), 400

    filter_value = request.args.get("done")

    connection = db_connection()
    try:
        if done is None:
            rows = connection.execute(
                "SELECT id, title, done, created_at "
                "FROM tasks ORDER BY id DESC"
            ).fetchall()
            return jsonify([dict(row) for row in rows])
        elif done is true:
            row = connection.execute(
                "SELECT id, title, done, created_at FROM tasks WHERE done = 1"
            )

    finally:
        connection.close()
 
 
@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400
 
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Укажите название задачи"}), 400
    title = title.strip()
    if len(title) > 100:
        return jsonify({"error": "Слишком длинное название"}), 400
 
    connection = db_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO tasks (title) VALUES (?)", (title,)
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, title, done, created_at "
            "FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return jsonify(dict(row)), 201
    finally:
        connection.close()

@app.get("/api/tasks/<int:task_id>")
def find_task(task_id):
    connection = db_connection()
    try:
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "id отсутствует"}), 404
        else:
            return jsonify(dict(row)), 200
    finally:
        connection.close()
 
@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON-объект"}), 400
    
    done = data.get("done")
    if type(done) is not bool:
        return jsonify({"error": "Ожидается bool(true or false)"}), 400

    connection = db_connection()
    try:
        cursor = connection.execute(
            "UPDATE tasks SET done = ? WHERE id = ?", (int(done), task_id,)
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "id отсутствует"}), 404

        row = connection.execute(
            "SELECT id, title, done, created_at FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        return jsonify(dict(row)), 200
    finally:
        connection.close()


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    connection = db_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM tasks WHERE id = ?", (task_id,)
        )
        connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "id отсутствует"}), 404
        else:
            return jsonify({"message": "задача удалена"}), 204
    finally: 
        connection.close()
 
initialize_db()
 
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
