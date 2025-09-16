from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, LoginView, MeView, AuthTestView


urlpatterns = [
    path('signup/', SignupView.as_view(), name='api-signup'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('me/', MeView.as_view(), name='api-me'),
    path('test/', AuthTestView.as_view(), name='api-auth-test'),
]


