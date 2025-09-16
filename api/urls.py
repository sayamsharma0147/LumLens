from django.urls import path, include


urlpatterns = [
    path('auth/', include('api.auth_urls')),
    path('photographers/', include('api.photographer_urls')),
    path('bookings/', include('api.booking_urls')),
]


