from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="register"),
    path("auth/verify", views.VerifyOtpView.as_view(), name="verify-otp"),
    path("auth/login", views.LoginView.as_view(), name="login"),
    path("auth/token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout", views.LogoutView.as_view(), name="logout"),
    path("profile", views.ProfileView.as_view(), name="profile"),
    path(
        "profile/change-phone/request",
        views.ChangePhoneRequestView.as_view(),
        name="change-phone-request",
    ),
    path(
        "profile/change-phone/confirm",
        views.ChangePhoneConfirmView.as_view(),
        name="change-phone-confirm",
    ),
    path("users", views.UserListView.as_view(), name="user-list"),
    path("users/<uuid:user_id>/role", views.UserRoleUpdateView.as_view(), name="user-role"),
]
