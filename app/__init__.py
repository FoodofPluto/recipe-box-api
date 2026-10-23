"""Recipe Box API — BE104 course skeleton.

A working Flask + SQLite CRUD API for recipes. It stores data perfectly —
and it trusts everyone. There is no authentication and no authorization yet.
That is the point: you will add both, lesson by lesson, in Units 2 and 3.
"""

from flask import Flask, g, jsonify, request, current_app
from password_utils import hash_password, verify_password
from werkzeug.security import generate_password_hash, check_password_hash
import os
import jwt
import sqlite3
from app.config import config_map
from app.db import init_db
from app.extensions import db, migrate
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from app.models import Recipe, User


load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")

def create_app(config_name="development"):
    from app.routes.auth import auth_bp
    from app.routes.recipes import recipes_bp
    from app.db import init_db
    from app.extensions import cache

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
#    init_db(app)
    

    app.register_blueprint(auth_bp)
    app.register_blueprint(recipes_bp)
    

    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()



    @app.get("/")
    def hello():
        return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})


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


    @app.post("/login")
    def login():
        data = request.get_json() or {}

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "username and password are required"}, 400

        user = User.query.filter_by(username=username).first()

        # Generic error message – same for unknown user and wrong password
        generic_error = {"error": "Invalid username or password"}

        if user is None:
            return generic_error, 401

        if not check_password_hash(user.password_hash, password):
            return generic_error, 401

        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=30),
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "token": token,
        }, 200
    
    @app.patch("/recipes/<int:recipe_id>")
#    @token_required
    def update_recipe(recipe_id):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "a JSON body is required"}), 400

#        # 1. Ownership / admin check (same rule as delete)
#        user_id = g.user_id
#        role = g.role


        user_id = 1
        role = "admin"
#        
#   End of Token Bypass.        
        recipe = Recipe.query.get(recipe_id)
        if recipe is None:
            return jsonify({"error": "recipe not found"}), 404

        is_owner = recipe.user_id == user_id
        is_admin = role == "admin"

        if not (is_owner or is_admin):
            return jsonify({"error": "forbidden: not owner or admin"}), 403

                
        # 2. Apply updates directly to the recipe object
        updated = False

        for column in ("title", "ingredients", "instructions"):
            if column in data:
                setattr(recipe, column, data[column])
                updated = True

        if "is_public" in data:
            recipe.is_public = 1 if data["is_public"] else 0
            updated = True

        if not updated:
            return jsonify({"error": "nothing to update"}), 400

        try:
            db.session.commit()
        except Exception:
            return jsonify({"error": "a recipe with that title already exists"}), 409

        return jsonify(recipe_to_dict(recipe))

#        # cur.rowcount should be > 0 if we passed the earlier 404, but we can keep this:
#       if cur.rowcount == 0:
#            return jsonify({"error": "recipe not found"}), 404
#
#        row = db.execute(
#            "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
#        ).fetchone()
#        return jsonify(recipe_to_dict(row))


    @app.delete("/recipes/<int:recipe_id>")
    @token_required
    def delete_recipe(recipe_id):

        user_id = g.user_id
        role = g.role

        # 2. Load the recipe first (ORM)
        recipe = Recipe.query.get(recipe_id)
        if recipe is None:
            # No such recipe at all
            return jsonify({"error": "recipe not found"}), 404

        is_owner = recipe.user_id == user_id
        is_admin = role == "admin"

        # 3. Now it's safe to delete (ORM)
        db.session.delete(recipe)
        db.session.commit()

        return "", 204

    # for the moment, just this line

    return app


