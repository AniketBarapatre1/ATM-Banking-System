# storage_sqlite.py
import sqlite3
from pathlib import Path
from datetime import date, datetime

DB_PATH = Path("fitness.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
  username    TEXT UNIQUE NOT NULL,
  pin_hash    TEXT NOT NULL,
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exercises (
  exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
  category    TEXT,
  name        TEXT UNIQUE NOT NULL,
  cal_per_min REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS workouts (
  workout_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL,
  exercise    TEXT NOT NULL,
  date        TEXT NOT NULL,
  duration    INTEGER NOT NULL,
  calories    REAL NOT NULL,
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, date);
"""

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(exercises_dict=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    if exercises_dict:
        for cat, items in exercises_dict.items():
            for name, cal in items.items():
                cur.execute(
                    "INSERT OR IGNORE INTO exercises(category, name, cal_per_min) VALUES (?, ?, ?)",
                    (cat, name, float(cal))
                )
    conn.commit()
    conn.close()

# simple pbkdf2 helpers (compatible with ATM utils if you have it)
import hashlib, os, hmac
ITERATIONS = 600000

def hash_pin(pin, salt=None):
    if salt is None:
        salt = os.urandom(8).hex()
    h = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), bytes.fromhex(salt), ITERATIONS).hex()
    return f"{salt}${h}"

def check_pin(pin, stored):
    try:
        salt = stored.split('$', 1)[0]
        return hmac.compare_digest(hash_pin(pin, salt), stored)
    except Exception:
        return False

# User ops
def create_user(username, pin):
    ph = hash_pin(pin)
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users(username, pin_hash) VALUES (?, ?)", (username, ph))
        conn.commit()
        uid = cur.lastrowid
    except sqlite3.IntegrityError:
        uid = None
    conn.close()
    return uid

def authenticate_user(username, pin):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, pin_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if check_pin(pin, row["pin_hash"]):
        return row["user_id"]
    return None

def get_user_by_name(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username FROM users WHERE username = ?", (username,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

# Exercise helpers
def get_exercise_cal_per_min(name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT cal_per_min FROM exercises WHERE name = ?", (name,))
    r = cur.fetchone()
    conn.close()
    return float(r["cal_per_min"]) if r else None

# Workout CRUD
def add_workout(username, exercise_name, duration_minutes, on_date=None):
    if on_date is None:
        on_date = date.today().isoformat()
    user = get_user_by_name(username)
    if not user:
        raise ValueError("Unknown user")
    uid = user["user_id"]
    calpm = get_exercise_cal_per_min(exercise_name)
    if calpm is None:
        raise ValueError("Unknown exercise")
    calories = round(int(duration_minutes) * calpm, 2)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO workouts(user_id, exercise, date, duration, calories) VALUES (?, ?, ?, ?, ?)",
        (uid, exercise_name, on_date, int(duration_minutes), calories)
    )
    conn.commit()
    wid = cur.lastrowid
    conn.close()
    return wid, calories

def get_workouts(username, since=None, until=None):
    user = get_user_by_name(username)
    if not user:
        return []
    uid = user["user_id"]
    q = "SELECT workout_id, date, exercise, duration, calories FROM workouts WHERE user_id = ?"
    params = [uid]
    if since:
        q += " AND date(date) >= date(?)"
        params.append(since)
    if until:
        q += " AND date(date) <= date(?)"
        params.append(until)
    q += " ORDER BY date"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_workout(workout_id, duration_minutes):
    conn = get_conn()
    cur = conn.cursor()
    # fetch exercise name to recalc calories
    cur.execute("SELECT exercise FROM workouts WHERE workout_id = ?", (workout_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False
    exercise = r["exercise"]
    calpm = get_exercise_cal_per_min(exercise)
    if calpm is None:
        conn.close()
        return False
    new_cal = round(int(duration_minutes) * calpm, 2)
    cur.execute("UPDATE workouts SET duration = ?, calories = ? WHERE workout_id = ?",
                (int(duration_minutes), new_cal, workout_id))
    conn.commit()
    conn.close()
    return True

def delete_workout(workout_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM workouts WHERE workout_id = ?", (workout_id,))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0

def summary_last_7_days(username):
    user = get_user_by_name(username)
    if not user:
        return {"minutes": 0, "calories": 0.0}
    uid = user["user_id"]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      SELECT COALESCE(SUM(duration),0) as minutes, COALESCE(SUM(calories),0) as calories
      FROM workouts
      WHERE user_id = ? AND date(date) >= date('now', '-7 days')
    """, (uid,))
    r = cur.fetchone()
    conn.close()
    return {"minutes": int(r[0]), "calories": float(r[1])}
