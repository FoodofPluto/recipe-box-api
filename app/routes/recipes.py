from flask import Blueprint, jsonify, request
from app import JWT_SECRET
import jwt
from app.extensions import db, cache
from app.models import Recipe
from app.services.auth_service import get_jwt_payload_from_request
from app.services.recipe_service import get_recipes, get_recipe_by_id


recipes_bp = Blueprint("recipes", __name__, url_prefix="")

def recipe_to_dict(recipe):
    return {
        "id": recipe.id,
        "title": recipe.title,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "is_public": bool(recipe.is_public),
        "nickname": recipe.nickname
    }


@recipes_bp.get("/recipes")
@cache.cached(timeout=60)
def list_recipes():
    recipes = get_recipes() 
    return jsonify([recipe_to_dict(r) for r in recipes])

@recipes_bp.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    recipe = get_recipe_by_id(recipe_id)
    if recipe is None:
        return jsonify({"error": "recipe not found"}), 404
    return jsonify(recipe_to_dict(recipe)), 200

@recipes_bp.post("/recipes")
def create_recipe():
#    # 🔐 Use auth service instead of inline token logic
#    payload, error_response = get_jwt_payload_from_request()
#    if error_response is not None:
#        # error_response is (response_body, status_code)
#        return error_response

#    user_id = payload.get("user_id")
#    username = payload.get("username")


    # TEMP: bypass auth just for ORM work
    user_id = 1
    username = "seed_user"

    # 👇 existing recipe creation logic stays the same
    data = request.get_json(silent=True)
    if not data or not data.get("title") or not data.get("ingredients"):
        return jsonify({"error": "title and ingredients are required"}), 400

    try:
        recipe = Recipe(
            title=data["title"],
            ingredients=data["ingredients"],
            instructions=data.get("instructions", ""),
            is_public=1 if data.get("is_public", True) else 0,
            user_id=user_id,
        )
        db.session.add(recipe)
        db.session.commit()
        cache.clear()
    except Exception as e:
        print("ERROR CREATING RECIPE:", e)
        return jsonify({"error": "internal error creating recipe"}), 500

    return jsonify(recipe_to_dict(recipe)), 201


@recipes_bp.get("/health")
def health_check():
    return jsonify({"status": "ok"}), 200