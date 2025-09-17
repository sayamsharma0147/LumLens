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
            "email": "cust2@example.com",
            "password": "Passw0rd!",
            "displayName": "cust2",
            "role": "customer",
        },
        format="json",
    )
    # Create photographer
    client.post(
        "/api/auth/signup/",
        {
            "email": "photo2@example.com",
            "password": "Passw0rd!",
            "displayName": "photo2",
            "role": "photographer",
        },
        format="json",
    )
    User = get_user_model()
    return {
        "customer": User.objects.get(email="cust2@example.com"),
        "photographer": User.objects.get(email="photo2@example.com"),
    }


@pytest.fixture()
def tokens(client, users):
    t = {}
    r = client.post(
        "/api/auth/login/",
        {"email": "cust2@example.com", "password": "Passw0rd!"},
        format="json",
    )
    t["customer_access"] = r.json()["access"]
    r = client.post(
        "/api/auth/login/",
        {"email": "photo2@example.com", "password": "Passw0rd!"},
        format="json",
    )
    t["photographer_access"] = r.json()["access"]
    return t


def test_booking_creation_notifies_photographer(client, users, tokens):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r = client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-01-02",
            "time": "11:00:00",
        },
        format="json",
    )
    assert r.status_code == 201

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['photographer_access']}")
    r = client.get("/api/notifications/me/")
    assert r.status_code == 200
    items = r.json()
    assert any("New booking request" in n["message"] for n in items)


def test_accept_reject_complete_notify_customer(client, users, tokens):
    # Create booking
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r = client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-01-03",
            "time": "12:00:00",
        },
        format="json",
    )
    booking = r.json()

    # Photographer accepts
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['photographer_access']}")
    client.patch(f"/api/bookings/{booking['id']}/", {"status": "accepted"}, format="json")

    # Customer reads notifications and finds accepted
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r = client.get("/api/notifications/me/")
    assert any("accepted" in n["message"] for n in r.json())

    # Photographer completes -> customer notified
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['photographer_access']}")
    client.put(f"/api/bookings/{booking['id']}/complete/")

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r = client.get("/api/notifications/me/")
    assert any("Booking completed" in n["message"] for n in r.json())


def test_me_only_shows_own_and_mark_read(client, users, tokens):
    # Create a booking to generate photographer notification
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    client.post(
        "/api/bookings/",
        {
            "photographer": str(users["photographer"].uid),
            "date": "2030-02-01",
            "time": "10:00:00",
        },
        format="json",
    )

    # Photographer sees theirs
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['photographer_access']}")
    r = client.get("/api/notifications/me/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    # Mark first as read
    notif_id = items[0]["id"]
    r2 = client.patch(f"/api/notifications/{notif_id}/read/")
    assert r2.status_code == 200
    assert r2.json()["is_read"] is True

    # Customer should not be able to patch photographer's
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['customer_access']}")
    r3 = client.patch(f"/api/notifications/{notif_id}/read/")
    assert r3.status_code in (404, 403)


