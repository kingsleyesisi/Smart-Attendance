from django.urls import path
from .views import (
    SignupView,
    LoginView,
    ProfileDashboard,
    LogoutView,
    CoordinatorDashboard,
    TriggerReminderView,
    CourseListView,
    RegisterAllCoursesView,
    MyCoursesView,
)
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
    path(
        "profile/", ProfileDashboard.as_view(), name="test"
    ),  # Page redirected to after signup
    path("coordinator/", CoordinatorDashboard.as_view(), name="coordinator-check"),
    path("trigger-reminder/", TriggerReminderView.as_view(), name="trigger-reminder"),
    path("courses/", CourseListView.as_view(), name="course_list"),
    path(
        "courses/register/all/", RegisterAllCoursesView.as_view(), name="Register_all_courses"
    ),
    path("my-courses/", MyCoursesView.as_view(), name="my_courses"),
]
