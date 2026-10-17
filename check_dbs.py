from app import create_app
from app.db import init_db

dev_app = create_app("development")
print("dev:", dev_app.config["DATABASE"])

test_app = create_app("testing")
print("test:", test_app.config["DATABASE"])

test_app = create_app("testing")
init_db(test_app)