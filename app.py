```python
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime
from pathlib import Path

# ----------------------------------
# VIBECHAT CONFIGURATION
# ----------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "vibechat-change-this-secret-key"

socketio = SocketIO(app)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "vibechat.db"


# ----------------------------------
# DATABASE
# ----------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row):
    return dict(row) if row else None


# ----------------------------------
# HOME PAGE
# ----------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------------
# GET CHAT MESSAGES
# ----------------------------------

@app.route("/api/messages", methods=["GET"])
def get_messages():
    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, username, message, created_at
                FROM messages
                ORDER BY id DESC
                LIMIT 100
            """).fetchall()

        messages = [row_to_dict(row) for row in reversed(rows)]
        return jsonify(messages)

    except sqlite3.Error:
        app.logger.exception("Imeshindikana kupata ujumbe.")
        return jsonify({"error": "Imeshindikana kupata ujumbe."}), 500


# ----------------------------------
# GET ANNOUNCEMENTS
# ----------------------------------

@app.route("/api/announcements", methods=["GET"])
def get_announcements():
    try:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, title, content, created_at
                FROM announcements
                ORDER BY id DESC
                LIMIT 50
            """).fetchall()

        announcements = [row_to_dict(row) for row in reversed(rows)]
        return jsonify(announcements)

    except sqlite3.Error:
        app.logger.exception("Imeshindikana kupata matangazo.")
        return jsonify({"error": "Imeshindikana kupata matangazo."}), 500


# ----------------------------------
# SEND CHAT MESSAGE
# ----------------------------------

@socketio.on("chat_message")
def handle_chat_message(data):
    if not isinstance(data, dict):
        return

    username = str(data.get("username", "Mgeni")).strip()
    message = str(data.get("message", "")).strip()

    if not username:
        username = "Mgeni"

    # Limit message sizes
    username = username[:40]
    message = message[:2000]

    if not message:
        return

    created_at = current_time()

    try:
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (username, message, created_at)
                VALUES (?, ?, ?)
            """, (username, message, created_at))

            message_id = cursor.lastrowid
            conn.commit()

        new_message = {
            "id": message_id,
            "username": username,
            "message": message,
            "created_at": created_at
        }

        # Send the message to all connected users
        socketio.emit("new_message", new_message)

    except sqlite3.Error:
        app.logger.exception("Imeshindikana kuhifadhi ujumbe.")
        emit("server_error", {
            "message": "Ujumbe haukutumwa. Jaribu tena."
        })


# ----------------------------------
# PUBLISH ANNOUNCEMENT
# ----------------------------------

@socketio.on("publish_announcement")
def handle_announcement(data):
    if not isinstance(data, dict):
        return

    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()

    title = title[:120]
    content = content[:2000]

    if not title or not content:
        emit("server_error", {
            "message": "Jaza kichwa na maelezo ya tangazo."
        })
        return

    created_at = current_time()

    try:
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO announcements (title, content, created_at)
                VALUES (?, ?, ?)
            """, (title, content, created_at))

            announcement_id = cursor.lastrowid
            conn.commit()

        announcement = {
            "id": announcement_id,
            "title": title,
            "content": content,
            "created_at": created_at
        }

        socketio.emit("new_announcement", announcement)

    except sqlite3.Error:
        app.logger.exception("Imeshindikana kuhifadhi tangazo.")
        emit("server_error", {
            "message": "Tangazo halijachapishwa. Jaribu tena."
        })


# ----------------------------------
# START VIBECHAT
# ----------------------------------

if __name__ == "__main__":
    init_db()

    print("=" * 40)
    print("       VIBECHAT IMEANZA!")
    print(" Fungua: http://127.0.0.1:5000")
    print("=" * 40)

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
```
