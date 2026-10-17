import os
import sqlite3

DEV_DB = "recipes.db"
TEST_DB = "test_recipes.db"

print("DEV DB:", os.path.abspath(DEV_DB))
print("TEST DB:", os.path.abspath(TEST_DB))

for name in (DEV_DB, TEST_DB):
    print("\n=== ", name, " ===")
    conn = sqlite3.connect(name)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM users")
        print("users:", c.fetchone()[0])
    except Exception as e:
        print("users error:", e)
    try:
        c.execute("SELECT COUNT(*) FROM recipes")
        print("recipes:", c.fetchone()[0])
    except Exception as e:
        print("recipes error:", e)
    conn.close()