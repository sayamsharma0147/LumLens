from django.urls import include, path

urlpatterns = [
    path("auth/", include("api.auth_urls")),
    path("photographers/", include("api.photographer_urls")),
    path("bookings/", include("api.booking_urls")),
    path("notifications/", include("api.notifications_urls")),
]
