from app.core.security import hash_password, verify_password, create_access_token

def test_password_hash_verify():
    pw_hashed = hash_password("secretpw123")
    assert verify_password("secretpw123", pw_hashed)
    assert not verify_password("wrong", pw_hashed)

def test_jwt_created():
    token = create_access_token("42", minutes=1, extra={"email": "a@b.com"})
    assert isinstance(token, str) and len(token) > 20
