from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    ProfileView,
    RegisterView,
    verify_email,
)

app_name = "users"

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("verify/email", verify_email, name="verify_email"),
    path("profile", ProfileView.as_view(), name="profile"),
    # JWT
    path("token/login", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/logout", LogoutAPIView.as_view(), name="logout"),
    path("token/refresh", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify", TokenVerifyView.as_view(), name="token_verify"),
    # oauth
    # # naver
    # path(
    #     "naver/login/", oauth_views.NaverLoginRedirectView.as_view(), name="naver_login"
    # ),
    # path("naver/callback/", oauth_views.naver_callback, name="naver_callback"),
    # path("nickname/", oauth_views.oauth_nickname, name="nickname"),
]
