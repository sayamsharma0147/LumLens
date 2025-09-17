from django.urls import path

from .views import NotificationMarkReadView, NotificationMeListView

urlpatterns = [
    path("me/", NotificationMeListView.as_view(), name="notifications-me"),
    path(
        "<uuid:id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
]
