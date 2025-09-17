import os
import json
from datetime import date, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402


def print_step(title: str, data):
    print(f"\n=== {title} ===")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(str(data))


def main():
    client = APIClient()

    # Health
    resp = client.get("/api/health/")
    print_step("health", resp.json())

    # Signup customer
    customer_email = "customer@example.com"
    photographer_email = "photog@example.com"
    for email, role in (
        (customer_email, "customer"),
        (photographer_email, "photographer"),
    ):
        client.post(
            "/api/auth/signup/",
            {
                "email": email,
                "password": "Passw0rd!",
                "displayName": email.split("@")[0],
                "role": role,
            },
            format="json",
        )

    # Login customer
    resp = client.post(
        "/api/auth/login/", {"email": customer_email, "password": "Passw0rd!"}, format="json"
    )
    assert resp.status_code == 200, (resp.status_code, resp.content)
    tokens = resp.json()
    print_step("login_customer", tokens)
    access = tokens["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    # Me
    resp = client.get("/api/auth/me/")
    assert resp.status_code == 200, (resp.status_code, resp.content)
    print_step("me_customer", resp.json())

    # Login photographer and ensure profile exists
    client.credentials()
    resp = client.post(
        "/api/auth/login/", {"email": photographer_email, "password": "Passw0rd!"}, format="json"
    )
    assert resp.status_code == 200, (resp.status_code, resp.content)
    photographer_access = resp.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {photographer_access}")

    # GET photographer me (creates default profile if missing)
    resp = client.get("/api/photographers/me/")
    assert resp.status_code == 200, (resp.status_code, resp.content)
    print_step("photographer_profile_get", resp.json())

    # Update photographer profile
    resp = client.put(
        "/api/photographers/me/",
        {"bio": "Pro photographer", "profile_image": "", "availableForBooking": True},
        format="json",
    )
    assert resp.status_code in (200, 202), (resp.status_code, resp.content)
    print_step("photographer_profile_update", resp.json())

    # Customer creates booking
    User = get_user_model()
    photographer = User.objects.get(email=photographer_email)
    client.credentials()
    resp = client.post(
        "/api/auth/login/", {"email": customer_email, "password": "Passw0rd!"}, format="json"
    )
    access = resp.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    resp = client.post(
        "/api/bookings/",
        {
            "photographer": str(photographer.uid),
            "date": date.today().isoformat(),
            "time": time(10, 0).isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 201, (resp.status_code, resp.content)
    booking = resp.json()
    print_step("booking_create", booking)

    # Customer list bookings
    resp = client.get("/api/bookings/me/")
    assert resp.status_code == 200
    print_step("booking_list_customer", resp.json())

    # Photographer accepts booking
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {photographer_access}")
    booking_id = booking["id"]
    resp = client.patch(
        f"/api/bookings/{booking_id}/",
        {"status": "accepted"},
        format="json",
    )
    assert resp.status_code == 200, (resp.status_code, resp.content)
    print_step("booking_status_update", resp.json())

    # Photographer completes booking
    resp = client.put(f"/api/bookings/{booking_id}/complete/")
    assert resp.status_code == 200, (resp.status_code, resp.content)
    print_step("booking_complete", resp.json())


if __name__ == "__main__":
    main()


