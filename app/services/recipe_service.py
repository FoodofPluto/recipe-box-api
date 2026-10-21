from app.models import Recipe

def get_recipes(limit=None):
    query = Recipe.query.order_by(Recipe.id)
    if limit is not None:
        query = query.limit(limit)
    return query.all() 

def get_recipe_by_id(recipe_id):
    query = Recipe.query.filter_by(id=recipe_id)
    recipe = query.first()
    return recipe    
    