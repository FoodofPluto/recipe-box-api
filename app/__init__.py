"""Recipe Box API — BE104 course skeleton.

A working Flask + SQLite CRUD API for recipes. It stores data perfectly —
and it trusts everyone. There is no authentication and no authorization yet.
That is the point: you will add both, lesson by lesson, in Units 2 and 3.
"""

import sqlite3

from flask import Flask, g, jsonify, request
from password_utils import hash_password, verify_password
from werkzeug.security import generate_password_hash, check_password_hash
import os
import jwt
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
print("JWT_SECRET is:", repr(JWT_SECRET))

DATABASE = "recipes.db"

def create_app():
    app = Flask(__name__)
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(DATABASE)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db


    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()


    def recipe_to_dict(row):
        return {
            "id": row["id"],
            "title": row["title"],
            "ingredients": row["ingredients"],
            "instructions": row["instructions"],
            "is_public": bool(row["is_public"]),
        }


    @app.get("/")
    def hello():
        return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})


    @app.get("/recipes")
    def list_recipes():
        rows = get_db().execute("SELECT * FROM recipes ORDER BY id").fetchall()
        return jsonify([recipe_to_dict(r) for r in rows])


    @app.get("/recipes/<int:recipe_id>")
    def get_recipe(recipe_id):
        row = get_db().execute(
            "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "recipe not found"}), 404
        return jsonify(recipe_to_dict(row))

    def token_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "missing or invalid Authorization header"}), 401

            token = auth_header.split(" ", 1)[1]

            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "token expired, please log in again"}), 401
            except jwt.PyJWTError:
                return jsonify({"error": "invalid token"}), 401

            g.user_id = payload.get("user_id")
            g.role = payload.get("role", "user")

            return f(*args, **kwargs)
        return wrapper

    @app.post("/recipes")
    def create_recipe():
        # 🔐 1. Read Authorization header
        auth_header = request.headers.get("Authorization", "")

        # 🔐 2. Check for "Bearer <token>" format
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired, please log in again"}), 401
        except jwt.PyJWTError:
            return jsonify({"error": "invalid token"}), 401

        # 🔐 4. Extract identity from verified token
        user_id = payload.get("user_id")
        username = payload.get("username")
        # (For now we just keep these in local variables for possible use later.)

        # 👇 existing recipe creation logic
        data = request.get_json(silent=True)
        if not data or not data.get("title") or not data.get("ingredients"):
            return jsonify({"error": "title and ingredients are required"}), 400
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO recipes (title, ingredients, instructions, is_public, user_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    data["title"],
                    data["ingredients"],
                    data.get("instructions", ""),
                    1 if data.get("is_public", True) else 0,
                    user_id,
                ),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "a recipe with that title already exists"}), 409
        row = db.execute(
            "SELECT * FROM recipes WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return jsonify(recipe_to_dict(row)), 201

    @app.post("/register")
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

    @app.post("/login")
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

    @app.patch("/recipes/<int:recipe_id>")
    @token_required
    def update_recipe(recipe_id):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "a JSON body is required"}), 400

        db = get_db()

        # 1. Ownership / admin check (same rule as delete)
        user_id = g.user_id
        role = g.role

        row = db.execute(
            "SELECT id, user_id FROM recipes WHERE id = ?",
            (recipe_id,),
        ).fetchone()

        if row is None:
            return jsonify({"error": "recipe not found"}), 404

        is_owner = row["user_id"] == user_id
        is_admin = role == "admin"

        if not (is_owner or is_admin):
            return jsonify({"error": "forbidden: not owner or admin"}), 403

        # 2. Build update fields (same as before)
        fields, values = [], []
        for column in ("title", "ingredients", "instructions"):
            if column in data:
                fields.append(f"{column} = ?")
                values.append(data[column])
        if "is_public" in data:
            fields.append("is_public = ?")
            values.append(1 if data["is_public"] else 0)
        if not fields:
            return jsonify({"error": "nothing to update"}), 400

        values.append(recipe_id)

        try:
            cur = db.execute(
                f"UPDATE recipes SET {', '.join(fields)} WHERE id = ?", values
            )
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "a recipe with that title already exists"}), 409

        # cur.rowcount should be > 0 if we passed the earlier 404, but we can keep this:
        if cur.rowcount == 0:
            return jsonify({"error": "recipe not found"}), 404

        row = db.execute(
            "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
        ).fetchone()
        return jsonify(recipe_to_dict(row))


    @app.delete("/recipes/<int:recipe_id>")
    @token_required
    def delete_recipe(recipe_id):
        db = get_db()

        user_id = g.user_id
        role = g.role

        # 2. Load the recipe first
        row = db.execute(
            "SELECT id, user_id FROM recipes WHERE id = ?",
            (recipe_id,),
        ).fetchone()

        if row is None:
            # No such recipe at all
            return jsonify({"error": "recipe not found"}), 404

        is_owner = row["user_id"] == user_id
        is_admin = role == "admin"

        if not (is_owner or is_admin):
            # Recipe exists, token is valid, but user lacks permission
            return jsonify({"error": "forbidden: not owner or admin"}), 403

        # 3. Now it's safe to delete
        cur = db.execute(
            "DELETE FROM recipes WHERE id = ?",
            (recipe_id,),
        )
        db.commit()

        return "", 204

    # for the moment, just this line

    return app


