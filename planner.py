import sqlite3
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
DB_NAME = "todo.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                done INTEGER
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM tasks")
        row = cursor.fetchone()
        if row and row[0] == 0:
            cursor.executemany(
                "INSERT INTO tasks (id, title, date, description, done) VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "Здати дз з Python", "2026-10-15", "Я тепер вільна людина", 0),
                    (2, "Купити продукти", "2026-10-12", "Молоко, хліб, протеїн, філейка", 1)
                ]
            )
            conn.commit()

init_db()

class DatabaseTasksProxy:
    def __iter__(self):
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            return iter([{**dict(row), "done": bool(row["done"])} for row in cursor.fetchall()])

    def append(self, task):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (id, title, date, description, done)
                VALUES (?, ?, ?, ?, ?)
            """, (task["id"], task["title"], task["date"], task["description"], int(task["done"])))
            conn.commit()

TASKS = DatabaseTasksProxy()

def next_id():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM tasks")
        row = cursor.fetchone()
        return 1 if (row is None or row[0] is None) else row[0] + 1

@app.route("/")
def index():
    tasks = sorted(TASKS, key=lambda t: t["date"])
    return render_template("plan.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    date = request.form.get("date", "")
    description = request.form.get("description", "").strip()
    if title and date:
        TASKS.append({"id": next_id(), "title": title, "date": date,
                      "description": description, "done": False})
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT done FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row is not None:
            current_status = row[0]
            new_status = 0 if current_status == 1 else 1
            cursor.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_status, task_id))
            conn.commit()
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date = request.form.get("date", "")
        description = request.form.get("description", "").strip()
        if title and date:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tasks SET title = ?, date = ?, description = ? WHERE id = ?", (title, date, description, task_id))
                conn.commit()
        return redirect(url_for("index"))
    
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            return render_template("edit.html", task=dict(row))
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
