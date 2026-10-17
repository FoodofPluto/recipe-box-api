import sqlite3
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    ingredients TEXT NOT NULL,
    instructions TEXT NOT NULL DEFAULT '',
    is_public INTEGER NOT NULL DEFAULT 1,
    user_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user'
);
"""

def init_db(app):
    conn = sqlite3.connect(app.config["DATABASE"])
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(current_app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

def get_all_recipes():
    db = get_db()
    return db.execute(
        "SELECT * FROM recipes ORDER BY id"
    ).fetchall()


def insert_recipe(title, ingredients, instructions, is_public, user_id):
    db = get_db()
    cur = db.execute(
        "INSERT INTO recipes (title, ingredients, instructions, is_public, user_id)"
        " VALUES (?, ?, ?, ?, ?)",
        (title, ingredients, instructions, is_public, user_id),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return row