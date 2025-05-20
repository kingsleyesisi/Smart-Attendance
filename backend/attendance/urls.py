from django.urls import path
from .views import RegisterView, CustomTokenObtainPairView, approve_coordinator

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', CustomTokenObtainPairView.as_view(), name='login'),
    path('approve-coordinator/<int:user_id>', approve_coordinator, name='approve-coordinator'),
]