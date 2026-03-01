from django.urls import path
from .views import (
    MyTokenObtainPairView,
    MyTokenRefreshView,
    UserCreateView,
    CurrentUserView,
)

urlpatterns = [
    # Authentication
    path("token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", MyTokenRefreshView.as_view(), name="token_refresh"),
    # Users
    path("register/", UserCreateView.as_view(), name="user_register"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
]
