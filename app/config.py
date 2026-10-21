import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, "instance", "recipes.db")
DB_TEST_PATH = os.path.join(BASE_DIR, "instance", "recipes_test.db")
DEBUG_FLAG = True

class Config:
    DEBUG = DEBUG_FLAG
    TESTING = False
    DATABASE = DB_PATH

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DATABASE = DB_TEST_PATH
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE}"

class ProductionConfig(Config):
    pass

config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}