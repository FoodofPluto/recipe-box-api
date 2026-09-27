from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timedelta

# make sure JWT_SECRET is imported / defined where it already was

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # 1. Read Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]

        # 2. Decode and verify JWT
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired, please log in again"}), 401
        except jwt.PyJWTError:
            return jsonify({"error": "invalid token"}), 401

        # 3. Store identity on g so routes can use it
        g.user_id = payload.get("user_id")
        g.role = payload.get("role", "user")

        # 4. Hand off to the actual route
        return f(*args, **kwargs)

    return wrapper