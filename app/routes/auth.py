import sqlite3
import jwt

from flask import Blueprint, request, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import JWT_SECRET
from app.db import get_db



auth_bp = Blueprint("auth", __name__, url_prefix="")

@auth_bp.get("/debug/users")
def debug_users():
    db = get_db()
    rows = db.execute("SELECT id, username, email, role FROM users").fetchall()
    return {"users": [dict(r) for r in rows]}

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not username or not email or not password:
        return {"error": "username, email, and password are required"}, 400

    db = get_db()

    password_hash = generate_password_hash(password)

    try:
        cursor = db.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, role),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return {"error": "username or email already exists"}, 409   

    user_id = cursor.lastrowid
    return {"id": user_id, "username": username, "role": role}, 201

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "username and password are required"}, 400

    db = get_db()
    user = db.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    # Generic error message – same for unknown user and wrong password
    generic_error = {"error": "Invalid username or password"}

    if user is None:
        return generic_error, 401

    if not check_password_hash(user["password_hash"], password):
        return generic_error, 401

    # Success: create JWT with identity + expiry
    payload = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],  # 👈 carry role into the token
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],  # 👈 optional but handy for testing
        "token": token,
    }, 200