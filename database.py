import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path("fitmate.db")


# ==================================================
# Connection
# ==================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ==================================================
# Initialize Database
# ==================================================

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            goal TEXT,
            experience_level TEXT,
            training_days INTEGER,
            session_duration INTEGER,
            equipment TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            exercise TEXT NOT NULL,
            sets INTEGER,
            reps INTEGER,
            weight REAL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            plan_text TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ==================================================
# Users
# ==================================================

def create_user(
    name,
    goal,
    experience_level,
    training_days,
    session_duration,
    equipment
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (
            name,
            goal,
            experience_level,
            training_days,
            session_duration,
            equipment
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        goal,
        experience_level,
        training_days,
        session_duration,
        equipment
    ))

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return user_id


def update_user(
    user_id,
    name,
    goal,
    experience_level,
    training_days,
    session_duration,
    equipment
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET
            name = ?,
            goal = ?,
            experience_level = ?,
            training_days = ?,
            session_duration = ?,
            equipment = ?
        WHERE id = ?
    """, (
        name,
        goal,
        experience_level,
        training_days,
        session_duration,
        equipment,
        user_id
    ))

    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    return user


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        ORDER BY id
    """)

    users = cursor.fetchall()

    conn.close()

    return users


# ==================================================
# Progress
# ==================================================

def save_progress(
    user_id,
    date,
    exercise,
    sets,
    reps,
    weight,
    notes=""
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO progress (
            user_id,
            date,
            exercise,
            sets,
            reps,
            weight,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        date,
        exercise,
        sets,
        reps,
        weight,
        notes
    ))

    conn.commit()
    conn.close()


def get_user_progress(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM progress
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (user_id,))

    progress = cursor.fetchall()

    conn.close()

    return progress


# ==================================================
# Workout Plans
# ==================================================

def save_workout_plan(
    user_id,
    plan_text
):
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    cursor.execute("""
        INSERT INTO workout_plans (
            user_id,
            created_at,
            plan_text
        )
        VALUES (?, ?, ?)
    """, (
        user_id,
        created_at,
        plan_text
    ))

    plan_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return plan_id


def get_latest_workout_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM workout_plans
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    plan = cursor.fetchone()

    conn.close()

    return plan


# ==================================================
# Test
# ==================================================

if __name__ == "__main__":
    init_db()

    print(
        "FitMate database initialized successfully."
    )