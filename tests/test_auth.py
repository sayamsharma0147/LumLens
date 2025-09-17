import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture()
def client():
    return APIClient()


def test_signup_creates_customer(client):
    resp = client.post(
        "/api/auth/signup/",
        {
            "email": "newuser@example.com",
            "password": "Passw0rd!",
            "displayName": "newuser",
            "role": "customer",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content


def test_login_returns_jwt_tokens(client):
    # Ensure user exists
    client.post(
        "/api/auth/signup/",
        {
            "email": "loginuser@example.com",
            "password": "Passw0rd!",
            "displayName": "loginuser",
            "role": "customer",
        },
        format="json",
    )

    resp = client.post(
        "/api/auth/login/",
        {"email": "loginuser@example.com", "password": "Passw0rd!"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert "access" in data and "refresh" in data


def test_me_with_valid_token_returns_user(client):
    client.post(
        "/api/auth/signup/",
        {
            "email": "meuser@example.com",
            "password": "Passw0rd!",
            "displayName": "meuser",
            "role": "customer",
        },
        format="json",
    )
    login = client.post(
        "/api/auth/login/",
        {"email": "meuser@example.com", "password": "Passw0rd!"},
        format="json",
    )
    access = login.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    resp = client.get("/api/auth/me/")
    assert resp.status_code == 200
    user = resp.json()
    assert user["email"] == "meuser@example.com"
    assert user["role"] == "customer"
