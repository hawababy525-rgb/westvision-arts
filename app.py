"""
WESTVISION ARTS - Chat & Media App (backend)
--------------------------------------------
Flask + Flask-SocketIO + SQLite.

Vipengele:
  - Kuingia kwa password ya kikundi
  - Group chat (wote wanaona na kuchangia)
  - Private chat kwa Owner tu (inafunguliwa kwa password 'moud1234')
  - Kutuma picha, link, video fupi (<=8s), na record ya sauti
  - Sehemu ya matangazo ya kazi (picha + link) inayoonekana kwa wote
  - GPS Geolocation Tracking kwa ajili ya Owner kufuatilia wanachama
  - PWA: inaweza kusakinishwa kwenye simu na kompyuta kama app
"""
import os
import sqlite3
import time
import uuid

from flask import (Flask, render_template, request, jsonify, session,
                   send_from_directory, abort)
from flask_socketio import SocketIO, join_room, emit
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("WV_DATA_DIR", BASE)
os.makedirs(DATA_DIR, exist_ok=True)
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "westvision.db")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---- Config / passwords (badilisha kupitia environment variables) ----
GROUP_PASSWORD = os.environ.get("WV_GROUP_PASSWORD", "11223344")
OWNER_PASSWORD = os.environ.get("WV_OWNER_PASSWORD", "MOUD1234")
JOIN_CODE = os.environ.get("WV_JOIN_CODE", "tanganyika")
QUICK_LOGIN_NAME = os.environ.get("WV_QUICK_LOGIN_NAME", "tanganyika").strip().lower()
QUICK_LOGIN_PIN = os.environ.get("WV_QUICK_LOGIN_PIN", "11223344")
SECRET_KEY = os.environ.get("WV_SECRET", "badilisha-siri-hii-kabla-ya-matumizi")

TAGLINE = ("WESTVISION ARTS ni kikundi cha wasanii mahiri kutoka Tanganyika "
           "Magharibi kilichojitolea kuleta burudani, ubunifu, na maono mapya "
           "kupitia filamu, uigizaji, na muziki.")

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp",
               "mp4", "webm", "mov",
               "ogg", "mp3", "wav", "m4a"}
MAX_UPLOAD = 25 * 1024 * 1024  # 25 MB

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("WV_HTTPS", "0") == "1"
app.permanent_session_lifetime = 60 * 60 * 24 * 30
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD
socketio = SocketIO(app, cors_allowed_origins=[], max_http_buffer_size=MAX_UPLOAD)


# ---------------- Database ----------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created REAL);
        CREATE TABLE IF NOT EXISTS messages(
            id TEXT PRIMARY KEY, username TEXT, text TEXT,
            media_url TEXT, media_type TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS private(
            id TEXT PRIMARY KEY, thread TEXT, sender TEXT, role TEXT,
            text TEXT, media_url TEXT, media_type TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS announcements(
            id TEXT PRIMARY KEY, username TEXT, title TEXT, text TEXT,
            image_url TEXT, link TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS user_locations(
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT,
            latitude TEXT, longitude TEXT, updated REAL);
        """)


init_db()


def now():
    return time.time()


def hhmm(ts):
    return time.strftime("%H:%M", time.localtime(ts))


# ---------------- Helpers ----------------
def logged_in():
    return session.get("auth") is True


def is_owner():
    return session.get("owner") is True


def require_login():
    if not logged_in():
        abort(401)


# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template("index.html", tagline=TAGLINE)


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()[:254]
    code = (data.get("join_code") or "").strip().lower()
    password = data.get("password") or ""
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify(ok=False, error="Weka email halali."), 400
    if code != JOIN_CODE:
        return jsonify(ok=False, error="Code ya kujiunga si sahihi."), 403
    if len(password) < 8:
        return jsonify(ok=False, error="Password iwe na angalau herufi/namba 8."), 400
    with db() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            return jsonify(ok=False, error="Email hii imesajiliwa tayari. Ingia badala ya kujisajili tena."), 409
        next_id = c.execute("SELECT COALESCE(MAX(id),0)+1 FROM users").fetchone()[0]
        username = f"WESTVISION ARTS #{next_id:04d}"
        c.execute("INSERT INTO users(email,username,password_hash,created) VALUES(?,?,?,?)",
                  (email, username, generate_password_hash(password), now()))
    session.clear(); session.permanent = True
    session["auth"] = True; session["username"] = username; session["user_id"] = next_id
    return jsonify(ok=True, username=username)


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    login_name = (data.get("username") or data.get("email") or "").strip().lower()[:254]
    password = str(data.get("password") or "")
    if login_name == QUICK_LOGIN_NAME and password == QUICK_LOGIN_PIN:
        session.clear(); session.permanent = True
        session["auth"] = True
        session["username"] = "Tanganyika"
        session["user_id"] = None
        return jsonify(ok=True, username="Tanganyika")

    email = login_name
    with db() as c:
        user = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(ok=False, error="Taarifa si sahihi. Tumia Tanganyika na PIN uliyopewa."), 403
    session.clear(); session.permanent = True
    session["auth"] = True; session["username"] = user["username"]; session["user_id"] = user["id"]
    return jsonify(ok=True, username=user["username"])


@app.route("/api/owner-unlock", methods=["POST"])
def api_owner_unlock():
    require_login()
    data = request.get_json(force=True)
    if (data.get("password") or "") != OWNER_PASSWORD:
        return jsonify(ok=False, error="Password ya owner si sahihi"), 403
    session["owner"] = True
    return jsonify(ok=True)


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify(ok=True)


@app.route("/api/me")
def api_me():
    return jsonify(auth=logged_in(), owner=is_owner(),
                   username=session.get("username", ""))


# ---- GPS Location Tracking Endpoints ----
@app.route("/api/save-location", methods=["POST"])
def api_save_location():
    if not logged_in():
        return jsonify(ok=False), 401
    data = request.get_json(silent=True) or {}
    lat = str(data.get("latitude") or "")
    lon = str(data.get("longitude") or "")
    if not lat or not lon:
        return jsonify(ok=False, error="Eneo halijapatikana"), 400
    username = session.get("username", "Mwanachama")
    ts = now()
    with db() as c:
        existing = c.execute("SELECT 1 FROM user_locations WHERE username=?", (username,)).fetchone()
        if existing:
            c.execute("UPDATE user_locations SET latitude=?, longitude=?, updated=? WHERE username=?",
                      (lat, lon, ts, username))
        else:
            c.execute("INSERT INTO user_locations(username, latitude, longitude, updated) VALUES(?,?,?,?)",
                      (username, lat, lon, ts))
    return jsonify(ok=True)


@app.route("/api/owner/locations")
def api_owner_locations():
    if not is_owner():
        return jsonify(ok=False, error="Ruhusa imekataliwa"), 403
    with db() as c:
        rows = c.execute("SELECT username, latitude, longitude, updated FROM user_locations ORDER BY updated DESC").fetchall()
    locations = [
        {
            "username": r["username"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "time": hhmm(r["updated"])
        } for r in rows
    ]
    return jsonify(ok=True, locations=locations)


def _save_upload(file):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        return None
    name = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_DIR, secure_filename(name)))
    return name


@app.route("/api/upload", methods=["POST"])
def api_upload():
    require_login()
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(ok=False, error="Hakuna faili"), 400
    name = _save_upload(f)
    if not name:
        return jsonify(ok=False, error="Aina ya faili hairuhusiwi"), 400
    return jsonify(ok=True, url=f"/uploads/{name}")


@app.route("/uploads/<path:fname>")
def serve_upload(fname):
    require_login()
    return send_from_directory(UPLOAD_DIR, fname)


@app.route("/api/messages", methods=["POST"])
def api_send_message():
    require_login()
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()[:2000]
    media_url = (data.get("media_url") or "")[:300] or None
    media_type = (data.get("media_type") or "")[:20] or None
    if not text and not media_url:
        return jsonify(ok=False, error="Andika ujumbe au ambatisha faili."), 400
    mid, ts = uuid.uuid4().hex, now()
    username = session.get("username", "Mwanachama")
    with db() as c:
        c.execute("INSERT INTO messages VALUES(?,?,?,?,?,?)",
                  (mid, username, text, media_url, media_type, ts))
    payload = {"id": mid, "username": username, "text": text,
               "media_url": media_url, "media_type": media_type, "time": hhmm(ts)}
    return jsonify(ok=True, message=payload)


@app.route("/api/history")
def api_history():
    require_login()
    with db() as c:
        rows = c.execute(
            "SELECT * FROM messages ORDER BY created ASC LIMIT 300").fetchall()
    return jsonify(messages=[_msg_dict(r) for r in rows])


@app.route("/api/announcements", methods=["POST"])
def api_create_announcement():
    require_login()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()[:120]
    text = (data.get("text") or "").strip()[:1000]
    image_url = (data.get("image_url") or "")[:300] or None
    link = (data.get("link") or "").strip()[:300] or None
    if link and not link.lower().startswith(("https://", "http://")):
        return jsonify(ok=False, error="Link ianze na https:// au http://."), 400
    if not title and not text and not image_url and not link:
        return jsonify(ok=False, error="Weka kichwa, maelezo, picha au link."), 400
    aid, ts = uuid.uuid4().hex, now()
    username = session.get("username", "Mwanachama")
    with db() as c:
        c.execute("INSERT INTO announcements VALUES(?,?,?,?,?,?,?)",
                  (aid, username, title, text, image_url, link, ts))
    payload = {"id": aid, "username": username, "title": title, "text": text,
               "image_url": image_url, "link": link, "timestr": hhmm(ts)}
    return jsonify(ok=True, item=payload)


@app.route("/api/announcements")
def api_announcements():
    require_login()
    with db() as c:
        rows = c.execute(
            "SELECT * FROM announcements ORDER BY created DESC LIMIT 100").fetchall()
    return jsonify(items=[dict(r) | {"timestr": hhmm(r["created"])} for r in rows])


@app.route("/api/private", methods=["POST"])
def api_send_private():
    require_login()
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()[:2000]
    media_url = (data.get("media_url") or "")[:300] or None
    media_type = (data.get("media_type") or "")[:20] or None
    me = session.get("username", "Mwanachama")
    if is_owner():
        thread = (data.get("thread") or "").strip()[:100]
        role, sender = "owner", "Owner"
        if not thread:
            return jsonify(ok=False, error="Chagua mwanachama wa kumjibu."), 400
    else:
        thread, role, sender = me, "member", me
    if not text and not media_url:
        return jsonify(ok=False, error="Andika ujumbe kwanza."), 400
    pid, ts = uuid.uuid4().hex, now()
    with db() as c:
        c.execute("INSERT INTO private VALUES(?,?,?,?,?,?,?,?)",
                  (pid, thread, sender, role, text, media_url, media_type, ts))
    payload = {"id": pid, "thread": thread, "sender": sender, "role": role,
               "text": text, "media_url": media_url, "media_type": media_type, "time": hhmm(ts)}
    return jsonify(ok=True, message=payload)


@app.route("/api/private")
def api_private():
    require_login()
    with db() as c:
        if is_owner():
            threads = {}
            for r in c.execute("SELECT * FROM private ORDER BY created ASC"):
                threads.setdefault(r["thread"], []).append(_pm_dict(r))
            return jsonify(owner=True, threads=threads)
        me = session.get("username")
        rows = c.execute("SELECT * FROM private WHERE thread=? ORDER BY created ASC",
                         (me,)).fetchall()
    return jsonify(owner=False, thread=me, messages=[_pm_dict(r) for r in rows])


@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(os.path.join(BASE, "static"),
                               "manifest.webmanifest",
                               mimetype="application/manifest+json")


@app.route("/sw.js")
def sw():
    return send_from_directory(os.path.join(BASE, "static"), "sw.js",
                               mimetype="application/javascript")


def _msg_dict(r):
    return {"id": r["id"], "username": r["username"], "text": r["text"],
            "media_url": r["media_url"], "media_type": r["media_type"],
            "time": hhmm(r["created"])}


def _pm_dict(r):
    return {"id": r["id"], "thread": r["thread"], "sender": r["sender"],
            "role": r["role"], "text": r["text"], "media_url": r["media_url"],
            "media_type": r["media_type"], "time": hhmm(r["created"])}


# ---------------- Socket.IO ----------------
@socketio.on("join")
def on_join():
    if not logged_in():
        return
    join_room("group")
    me = session.get("username")
    join_room(f"pm:{me}")
    if is_owner():
        join_room("owners")
    emit("system", {"msg": f"{me} amejiunga", "time": hhmm(now())}, to="group")


@socketio.on("group_message")
def on_group_message(data):
    if not logged_in():
        return
    me = session.get("username")
    text = (data.get("text") or "").strip()[:2000]
    media_url = (data.get("media_url") or "")[:300] or None
    media_type = (data.get("media_type") or "")[:20] or None
    if not text and not media_url:
        return
    mid = uuid.uuid4().hex
    ts = now()
    with db() as c:
        c.execute("INSERT INTO messages VALUES(?,?,?,?,?,?)",
                  (mid, me, text, media_url, media_type, ts))
    emit("group_message", {"id": mid, "username": me, "text": text,
                           "media_url": media_url, "media_type": media_type,
                           "time": hhmm(ts)}, to="group")


@socketio.on("private_send")
def on_private_send(data):
    if not logged_in():
        return
    me = session.get("username")
    text = (data.get("text") or "").strip()[:2000]
    media_url = (data.get("media_url") or "")[:300] or None
    media_type = (data.get("media_type") or "")[:20] or None
    if is_owner():
        thread = (data.get("thread") or "").strip()[:24]
        role = "owner"
        sender = "Owner"
    else:
        thread = me
        role = "member"
        sender = me
    if not thread or (not text and not media_url):
        return
    pid = uuid.uuid4().hex
    ts = now()
    with db() as c:
        c.execute("INSERT INTO private VALUES(?,?,?,?,?,?,?,?)",
                  (pid, thread, sender, role, text, media_url, media_type, ts))
    payload = {"id": pid, "thread": thread, "sender": sender, "role": role,
               "text": text, "media_url": media_url, "media_type": media_type,
               "time": hhmm(ts)}
    emit("private_message", payload, to=f"pm:{thread}")
    emit("private_message", payload, to="owners")


@socketio.on("announce")
def on_announce(data):
    if not logged_in():
        return
    me = session.get("username")
    title = (data.get("title") or "").strip()[:120]
    text = (data.get("text") or "").strip()[:1000]
    image_url = (data.get("image_url") or "")[:300] or None
    link = (data.get("link") or "").strip()[:300] or None
    if link and not link.lower().startswith(("https://", "http://")):
        link = None
    if not title and not image_url and not link:
        return
    aid = uuid.uuid4().hex
    ts = now()
    with db() as c:
        c.execute("INSERT INTO announcements VALUES(?,?,?,?,?,?,?)",
                  (aid, me, title, text, image_url, link, ts))
    emit("announce", {"id": aid, "username": me, "title": title, "text": text,
                      "image_url": image_url, "link": link,
                      "timestr": hhmm(ts)}, to="group")


@socketio.on("typing")
def on_typing():
    if not logged_in():
        return
    emit("typing", {"username": session.get("username")},
         to="group", include_self=False)


if __name__ == "__main__":
    socketio.run(app, host=os.environ.get("WV_HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "5000")), debug=False)
