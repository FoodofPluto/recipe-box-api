from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plaintext_password: str) -> str:
    """Return a one-way hash suitable for storing in password_hash."""
    return generate_password_hash(plaintext_password)


def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """Return True if the candidate matches the stored hash, else False."""
    return check_password_hash(stored_hash, candidate_password)