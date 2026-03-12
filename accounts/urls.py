from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    RegisterView,
    LogoutView,
    MeView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    AdminDashboardStatsView,
    AdminResetUserPasswordView,
    VerifyEmailView,
    ResendVerificationEmailView,
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('login/',           LoginView.as_view(),         name='auth-login'),
    path('register/',        RegisterView.as_view(),       name='auth-register'),
    path('logout/',          LogoutView.as_view(),         name='auth-logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),   name='token-refresh'),
    path('me/',              MeView.as_view(),             name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # ── Email Verification ────────────────────────────────────────────────────
    path('verify-email/',        VerifyEmailView.as_view(),            name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),

    # ── Password Reset ────────────────────────────────────────────────────────
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/',  ResetPasswordView.as_view(),  name='reset-password'),

    # ── Admin: Users ──────────────────────────────────────────────────────────
    path('users/',                       UserListView.as_view(),             name='user-list'),
    path('users/<int:pk>/',              UserDetailView.as_view(),           name='user-detail'),
    path('users/<int:pk>/reset-password/', AdminResetUserPasswordView.as_view(), name='admin-reset-password'),
    path('admin/stats/',                 AdminDashboardStatsView.as_view(),  name='admin-stats'),
]
