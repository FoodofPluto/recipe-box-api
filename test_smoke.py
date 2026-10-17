from app import create_app

test_app = create_app("testing")

with test_app.test_client() as client:
    register_resp = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "secret123",
            "role": "user",
        },
    )
    print("register:", register_resp.status_code, register_resp.json)

    login_resp = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "secret123",
        },
    )
    print("login:", login_resp.status_code, login_resp.json)

    recipes_resp = client.get("/recipes")
    print("recipes:", recipes_resp.status_code, recipes_resp.json)