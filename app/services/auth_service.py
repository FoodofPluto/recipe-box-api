# app/services/auth_service.py

import jwt
from flask import request, jsonify
from app import JWT_SECRET  # we'll clean this later

def get_jwt_payload_from_request():
    """
    Tries to read and verify a Bearer token from the Authorization header.

    Returns:
        (payload, None) on success
        (None, (response, status_code)) on error
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        error = jsonify({"error": "missing or invalid Authorization header"})
        return None, (error, 401)

    token = auth_header.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        error = jsonify({"error": "token expired, please log in again"})
        return None, (error, 401)
    except jwt.PyJWTError:
        error = jsonify({"error": "invalid token"})
        return None, (error, 401)

    return payload, None