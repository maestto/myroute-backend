from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_roundtrip() -> None:
    plain_password = "super-secret-password"
    password_hash = hash_password(plain_password)

    assert password_hash != plain_password
    assert verify_password(plain_password, password_hash)


def test_jwt_roundtrip_contains_subject() -> None:
    token = create_access_token("user@example.com")
    payload = decode_access_token(token)

    assert payload["sub"] == "user@example.com"
    assert "exp" in payload

