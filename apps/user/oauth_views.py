# views/oauth_views.py
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.views.generic import RedirectView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.oauth_mixins import (
    GoogleProviderInfoMixin,
    KaKaoProviderInfoMixin,
    NaverProviderInfoMixin,
)
from utils.random_nickname import generate_unique_numbered_nickname
from utils.responses.user import (
    LOGIN_SUCCESS,
    OAUTH_ACCESS_TOKEN_MISSING,
    OAUTH_CODE_OR_STATE_MISSING,
    OAUTH_EMAIL_MISSING,
    OAUTH_PROFILE_FAILED,
    OAUTH_TOKEN_FAILED,
)

User = get_user_model()


def get_social_login_params(provider_info, callback_url):
    state = signing.dumps(provider_info["state"])
    params = {
        "response_type": "code",
        "client_id": provider_info["client_id"],
        "redirect_uri": callback_url,
        "state": state,
    }
    if provider_info["name"] == "구글":
        params.update(
            {
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
            }
        )

    return params


class OauthLoginRedirectView(APIView, ABC):
    permission_classes = [AllowAny]

    @abstractmethod
    def get_provider_info(self):
        pass

    @swagger_auto_schema(
        operation_summary="소셜 로그인 리디렉션",
        operation_description="OAuth 제공자 로그인 페이지로 리디렉션됩니다.",
        responses={302: "로그인 페이지로 리디렉션"},
        tags=["소셜 로그인"],
    )
    def get(self, request, *args, **kwargs):
        provider_info = self.get_provider_info()
        callback_url = settings.FRONTEND_URL + provider_info["callback_url"]
        state = signing.dumps(provider_info["state"])
        params = get_social_login_params(provider_info, callback_url)
        login_url = f"{provider_info['login_url']}?{urlencode(params)}"
        return redirect(login_url)


class OAuthCallbackView(APIView, ABC):
    permission_classes = [AllowAny]

    @abstractmethod
    def get_provider_info(self):
        pass

    @swagger_auto_schema(
        operation_summary="소셜 로그인 콜백 처리",
        operation_description="프론트엔드에서 받은 code와 state를 통해 access_token을 발급받고, 유저 정보를 기반으로 로그인 처리 후 JWT 토큰을 반환합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["code", "state"],
            properties={
                "code": openapi.Schema(
                    type=openapi.TYPE_STRING, description="OAuth 인가 코드"
                ),
                "state": openapi.Schema(
                    type=openapi.TYPE_STRING, description="OAuth 요청 시 보낸 state 값"
                ),
            },
        ),
        responses={200: "로그인 성공", 400: "잘못된 요청", 401: "인증 실패"},
        tags=["소셜 로그인"],
    )
    def post(self, request, *args, **kwargs):
        code = request.data.get("code")
        state = request.data.get("state")

        if not code or not state:
            return Response(OAUTH_CODE_OR_STATE_MISSING, status=400)

        # 소셜로그인에 필요한 redirect_uri, client_id, grant_type 등의 provider_info 를 가져옴
        provider_info = self.get_provider_info()

        # state 검증 로직 필요 시 추가 (ex. signing.loads)

        # 엑세스 토큰 요청
        token_response = self.get_access_token(code, state, provider_info)
        if token_response.status_code != 200:
            return Response(OAUTH_TOKEN_FAILED, status=401)

        access_token = token_response.json().get("access_token")
        if not access_token:
            return Response(OAUTH_ACCESS_TOKEN_MISSING, status=401)

        # 프로필 요청
        profile_response = self.get_profile(access_token, provider_info)
        if profile_response.status_code != 200:
            return Response(OAUTH_PROFILE_FAILED, status=401)

        profile_data = profile_response.json()
        email, name, nickname = self.get_user_data(profile_data, provider_info)

        if not email:
            return Response(OAUTH_EMAIL_MISSING, status=400)

        # 기존 유저가 있으면 가져오고 없으면 새로 생성
        user, created = User.objects.get_or_create(email=email)
        if created:
            nickname = nickname or generate_unique_numbered_nickname()
            user.name = name
            user.nickname = nickname
            user.set_password(User.objects.make_random_password())
            user.is_active = True
            user.save()

        # JWT 토큰 발급
        refresh_token = RefreshToken.for_user(user)
        access_token = str(refresh_token.access_token)
        # 커스텀 CSRF 토큰 발급
        csrf_token = get_token(request=request)

        # 프론트로 토큰 전달
        response = Response(
            {
                **LOGIN_SUCCESS,
                "data": {
                    "access_token": access_token,
                    "csrf_token": csrf_token,
                },
            }
        )
        # 쿠키 추가
        response.set_cookie(
            key="refresh_token",
            value=str(refresh_token),
            httponly=True,
            secure=True,  # HTTPS 환경에서만 전송
            # secure=False,  # 로컬 개발 환경에 맞춰서 설정
            samesite="Lax",  # CSRF 공격 방지 설정
            path="/api/users/token",  # 필요한 경로에만 쿠키 사용
            max_age=60 * 60 * 24 * 1,  # 1일 (초 단위)
        )

        return response

    # 엑세스 토큰 가져오는 메서드
    def get_access_token(self, code, state, provider_info):
        """
        requests 라이브러리를 활용하여 Oauth2 API 플랫폼에 액세스 토큰을 요청하는 함수
        """
        if provider_info["name"] == "구글":
            return requests.post(
                provider_info["token_url"],
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "state": state,
                    "redirect_uri": settings.FRONTEND_URL
                    + provider_info["callback_url"],
                    "client_id": provider_info["client_id"],
                    "client_secret": provider_info["client_secret"],
                },
            )
        else:
            return requests.get(
                provider_info["token_url"],
                params={
                    "grant_type": "authorization_code",
                    "code": code,
                    "state": state,
                    "client_id": provider_info["client_id"],
                    "client_secret": provider_info["client_secret"],
                },
            )

    # 프로필 가져오는 메서드
    def get_profile(self, access_token, provider_info):
        """
        requests 라이브러리를 활용하여 Oauth2 API 플랫폼에 액세스 토큰을 사용하여 프로필 정보 조회를 요청하는 함수
        """

        return requests.get(
            provider_info["profile_url"],
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )

    def get_user_data(self, profile_data, provider_info):
        """
        Oauth2 API 플랫폼에서 가져온 프로필을 데이터 스키마에서 필요한 데이터를 추출하는 함수입니다.
        """
        # 각 provider의 프로필 데이터 처리 로직

        if provider_info["name"] == "구글":
            email = profile_data.get(provider_info["email_field"])
            name = profile_data.get(provider_info["name_field"], "")
            nickname = profile_data.get(provider_info["nickname_field"], None)
            return email, name, nickname

        elif provider_info["name"] == "네이버":
            profile_data = profile_data.get("response", {})
            email = profile_data.get(provider_info["email_field"])
            name = profile_data.get(provider_info["name_field"], "")
            nickname = profile_data.get(provider_info["nickname_field"], None)
            return email, name, nickname

        elif provider_info["name"] == "카카오":
            account_data = profile_data.get("kakao_account", {})
            email = account_data.get(provider_info["email_field"])
            profile_data = account_data.get("profile", {})
            name = profile_data.get(provider_info["name_field"], "")
            nickname = profile_data.get(provider_info["nickname_field"], None)
            return email, name, nickname

    # 성공 프론트 리다이렉트 url
    def get_frontend_success_url(self):
        return f"{self.get_provider_info()['frontend_redirect_url']}"

    # 실패 프론트 리다이렉트 url
    def get_frontend_fail_url(self):
        return f"{self.get_provider_info().get('frontend_fail_url', self.get_frontend_success_url())}"


# 카카오 로그인
class KakaoLoginRedirectView(KaKaoProviderInfoMixin, OauthLoginRedirectView):
    pass


# 카카오 콜백
class KakaoCallbackView(KaKaoProviderInfoMixin, OAuthCallbackView):
    pass


# 구글 로그인
class GoogleLoginRedirectView(GoogleProviderInfoMixin, OauthLoginRedirectView):
    pass


# 구글 콜백
class GoogleCallbackView(GoogleProviderInfoMixin, OAuthCallbackView):
    pass


# 네이버 로그인
class NaverLoginRedirectView(NaverProviderInfoMixin, OauthLoginRedirectView):
    pass


# 네이버 콜백
class NaverCallbackView(NaverProviderInfoMixin, OAuthCallbackView):
    pass
