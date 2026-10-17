class Config:
    DEBUG = False
    TESTING = False
    DATABASE = "recipes.db"   # moved here ✅

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DATABASE = "test_recipes.db"  # if you want a separate test DB

class ProductionConfig(Config):
    pass