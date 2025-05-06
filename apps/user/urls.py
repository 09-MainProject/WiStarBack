from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from . import oauth_google_views, oauth_kakao_views, oauth_naver_views
from .oauth_google_views import google_login_test_page
from .oauth_kakao_views import kakao_login_test_page
from .oauth_naver_views import naver_login_test_page, oauth_callback_test_page
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    ProfileView,
    RegisterView,
    VerifyEmailView,
)

app_name = "user"

urlpatterns = [
    path("signup", RegisterView.as_view(), name="signup"),
    # path("verify/email", verify_email, name="verify_email"),
    path("verify/email", VerifyEmailView.as_view(), name="verify_email"),
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
    # path("token/verify", TokenVerifyView.as_view(), name="token_verify"),
    # oauth naver
    path(
        "naver/login",
        oauth_naver_views.NaverLoginRedirectView.as_view(),
        name="naver_login",
    ),
    path("naver/callback", oauth_naver_views.naver_callback, name="naver_callback"),
    path("naver/login-test", naver_login_test_page, name="naver-login-test"),
    path("oauth/callback-test", oauth_callback_test_page, name="naver-callback-test"),
    # oauth kakao
    path(
        "kakao/login",
        oauth_kakao_views.KakaoLoginRedirectView.as_view(),
        name="kakao_login",
    ),
    path("kakao/callback", oauth_kakao_views.kakao_callback, name="kakao_callback"),
    # path("kakao/login-test", kakao_login_test_page, name="kakao-login-test"),
    # oauth google
    path(
        "google/login",
        oauth_google_views.GoogleLoginRedirectView.as_view(),
        name="google_login",
    ),
    path("google/callback", oauth_google_views.google_callback, name="google_callback"),
    # path("google/login-test", google_login_test_page, name="google-login-test"),
    # path("nickname/", oauth_views.oauth_nickname, name="nickname"),
]
