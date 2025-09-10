from django.urls import path
from .views import SignupView, LoginView, ProfileDashboard, LogoutView, CoordinatorDashboard, TriggerReminderView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Urls to endpoint
urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileDashboard.as_view(), name="test"), #test view for authentication (To be removed)
    path("coordinator/", CoordinatorDashboard.as_view(), name="coordinator-check"),
    path("trigger-reminder/", TriggerReminderView.as_view(), name="trigger-reminder"),
]
