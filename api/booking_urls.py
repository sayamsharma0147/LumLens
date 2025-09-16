from django.urls import path
from .views import BookingCreateView, BookingMeListView, BookingStatusUpdateView, BookingCompleteView, BookingsTestView


urlpatterns = [
    path('', BookingCreateView.as_view(), name='booking-create'),
    path('me/', BookingMeListView.as_view(), name='booking-me'),
    path('<uuid:id>/', BookingStatusUpdateView.as_view(), name='booking-status-update'),
    path('<uuid:id>/complete/', BookingCompleteView.as_view(), name='booking-complete'),
    path('test/', BookingsTestView.as_view(), name='bookings-test'),
]


