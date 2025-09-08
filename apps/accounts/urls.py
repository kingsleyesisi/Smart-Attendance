from django.urls import path
from .views import SignupView, LoginView, ProfileView, LogoutView, index
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

# Urls to endpoint
urlpatterns = [
    path("api/signup/", SignupView.as_view(), name="signup"),
    path("api/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/profile/", ProfileView.as_view(), name="test"), #test view for authentication
    path('', index, name='index')
]
