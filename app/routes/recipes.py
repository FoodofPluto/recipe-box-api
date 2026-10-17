from flask import Blueprint, jsonify, request
from app import JWT_SECRET
import jwt
import sqlite3
from app.db import get_all_recipes, insert_recipe, get_db
from app.services.auth_service import get_jwt_payload_from_request


recipes_bp = Blueprint("recipes", __name__, url_prefix="")

def recipe_to_dict(row):
        return {
            "id": row["id"],
            "title": row["title"],
            "ingredients": row["ingredients"],
            "instructions": row["instructions"],
            "is_public": bool(row["is_public"]),
        }

@recipes_bp.get("/recipes")
def list_recipes():
    rows = get_all_recipes()
    return jsonify([recipe_to_dict(r) for r in rows])

@recipes_bp.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()

    if row is None:
        return jsonify({"error": "recipe not found"}), 404

    return jsonify(recipe_to_dict(row)), 200

@recipes_bp.post("/recipes")
def create_recipe():
    # 🔐 Use auth service instead of inline token logic
    payload, error_response = get_jwt_payload_from_request()
    if error_response is not None:
        # error_response is (response_body, status_code)
        return error_response

    user_id = payload.get("user_id")
    username = payload.get("username")

    # 👇 existing recipe creation logic stays the same
    data = request.get_json(silent=True)
    if not data or not data.get("title") or not data.get("ingredients"):
        return jsonify({"error": "title and ingredients are required"}), 400

    try:
        row = insert_recipe(
        title=data["title"],
        ingredients=data["ingredients"],
        instructions=data.get("instructions", ""),
        is_public=1 if data.get("is_public", True) else 0,
        user_id=user_id,
        )
    except sqlite3.IntegrityError:
        return jsonify({"error": "a recipe with that title already exists"}), 409

    return jsonify(recipe_to_dict(row)), 201

@recipes_bp.get("/health")
def health_check():
    return jsonify({"status": "ok"}), 200