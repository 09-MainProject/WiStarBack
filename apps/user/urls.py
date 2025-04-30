from django.urls import path
from rest_framework_simplejwt.views import (
    TokenVerifyView,
)

from . import oauth_views
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    ProfileView,
    RegisterView,
    verify_email,
)

app_name = "user"

urlpatterns = [
    path("signup", RegisterView.as_view(), name="signup"),
    path("verify/email", verify_email, name="verify_email"),
    # POST /api/users/login/ -> 로그인
    # path("login", CustomTokenObtainPairView.as_view(), name="login"),
    # POST /api/users/login/ -> 로그아웃
    # path("logout", LogoutAPIView.as_view(), name="logout"),
    # GET /api/users/profile/ -> 내 프로필 조회
    # PATCH /api/users/me/ -> 내 프로필 수정
    path("profile", ProfileView.as_view(), name="profile"),
    # JWT
    path("token/login", CustomTokenObtainPairView.as_view(), name="token_login"),
    path("token/logout", LogoutAPIView.as_view(), name="token_logout"),
    path("token/refresh", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify", TokenVerifyView.as_view(), name="token_verify"),
    # oauth
    # # naver
    path(
        "naver/login/", oauth_views.NaverLoginRedirectView.as_view(), name="naver_login"
    ),
    path("naver/callback/", oauth_views.naver_callback, name="naver_callback"),
    path("nickname/", oauth_views.oauth_nickname, name="nickname"),
]
