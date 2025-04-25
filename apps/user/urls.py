
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .views import RegisterView, ProfileView, LogoutAPIView, verify_email, CustomTokenObtainPairView

app_name = 'user'

urlpatterns = [

    path("signup", RegisterView.as_view(), name="signup"),

    path('verify/email', verify_email, name='verify_email'),
    # POST /api/users/login/ -> 로그인
    path("login", CustomTokenObtainPairView.as_view(), name="login"),
    # POST /api/users/login/ -> 로그아웃
    path("logout", LogoutAPIView.as_view(), name="logout"),
    # GET /api/users/profile/ -> 내 프로필 조회
    # PATCH /api/users/me/ -> 내 프로필 수정
    path('profile', ProfileView.as_view(), name="profile"),

    # JWT
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify', TokenVerifyView.as_view(), name='token_verify'),

]