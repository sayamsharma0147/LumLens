from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, MeView, RoleAwareTokenObtainPairView


urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', RoleAwareTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
]


