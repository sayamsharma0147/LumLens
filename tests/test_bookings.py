import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture()
def client():
    return APIClient()


@pytest.fixture()
def users(client):
    # Create customer
    client.post(
        "/api/auth/signup/",
        {
            "email": "cust@example.com",
            "password": "Passw0rd!",
            "displayName": "cust",
            "role": "customer",
        },
        format="json",
    )
    # Create photographer
    client.post(
        "/api/auth/signup/",
        {
            "email": "photo@example.com",
            "password": "Passw0rd!",
            "displayName": "photo",
            "role": "photographer",
        },
        format="json",
    )
    User = get_user_model()
    return {
        "customer": User.objects.get(email="cust@example.com"),
        "photographer": User.objects.get(email="photo@example.com"),
    }


@pytest.fixture()
def tokens(client, users):
    t = {}
    r = client.post(
        "/api/auth/login/",
        {"email": "cust@example.com", "password": "Passw0rd!"},
        format="json",
    )
    t["customer_access"] = r.json()["access"]
    r = client.post(
        "/api/auth/login/",
        {"email": "photo@example.com", "password": "Passw0rd!"},
        format="json",
    )
    t["photographer_access"] = r.json()["access"]
    return t


def test_customer_can_create_booking(client, users, tokens):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    resp = client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-01-01",
            "time": "10:00:00",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content


def test_bookings_me_filters_by_role(client, users, tokens):
    # Create two bookings for the same photographer by the customer
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    for _ in range(2):
        client.post(
            "/api/bookings/",
            {
                "photographer": str(users["photographer"].uid),
                "date": "2030-01-01",
                "time": "10:00:00",
            },
            format="json",
        )
    # Customer sees their bookings
    r = client.get("/api/bookings/me/")
    assert r.status_code == 200
    customer_list = r.json()
    assert len(customer_list) >= 2

    # Photographer sees assigned bookings
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['photographer_access']}")
    r = client.get("/api/bookings/me/")
    assert r.status_code == 200
    photo_list = r.json()
    assert len(photo_list) >= 2
    # Ensure all bookings in list are assigned to the photographer
    assert all(b["photographer"] == str(users["photographer"].uid) for b in photo_list)


def test_photographer_can_accept_and_complete_booking(client, users, tokens):
    # Create booking as customer
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r = client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-01-01",
            "time": "10:00:00",
        },
        format="json",
    )
    booking = r.json()

    # Photographer accepts
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['photographer_access']}")
    r = client.patch(
        f"/api/bookings/{booking['id']}/", {"status": "accepted"}, format="json"
    )
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    # Photographer completes
    r = client.put(f"/api/bookings/{booking['id']}/complete/")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_customer_cannot_accept_or_complete(client, users, tokens):
    # Create booking as customer
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r = client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-01-01",
            "time": "10:00:00",
        },
        format="json",
    )
    booking = r.json()

    # Customer tries to accept
    r = client.patch(
        f"/api/bookings/{booking['id']}/", {"status": "accepted"}, format="json"
    )
    assert r.status_code in (403, 400)

    # Customer tries to complete
    r = client.put(f"/api/bookings/{booking['id']}/complete/")
    assert r.status_code in (403, 400)


def test_unauthorized_cannot_access_bookings(client, users):
    # No credentials
    r = client.get("/api/bookings/me/")
    assert r.status_code == 401
    r = client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-01-01",
            "time": "10:00:00",
        },
        format="json",
    )
    assert r.status_code == 401
