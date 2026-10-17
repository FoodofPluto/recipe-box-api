from app import create_app

app = create_app("development")  # or "production" later

if __name__ == "__main__":
    app.run()