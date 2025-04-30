from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.generic import RedirectView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

NAVER_CALLBACK_URL = "/users/naver/callback/"
NAVER_STATE = "naver_login"
NAVER_LOGIN_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"


class NaverLoginRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        domain = self.request.scheme + "://" + self.request.META.get("HTTP_HOST", "")
        domain = domain.replace("localhost", "127.0.0.1")
        callback_url = domain + NAVER_CALLBACK_URL
        state = signing.dumps(NAVER_STATE)

        params = {
            "response_type": "code",
            "client_id": settings.NAVER_CLIENT_ID,
            "redirect_uri": callback_url,
            "state": state,
        }

        return f"{NAVER_LOGIN_URL}?{urlencode(params)}"


def naver_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    if NAVER_STATE != signing.loads(state):
        raise Http404

    access_token = get_naver_access_token(code, state)
    profile = get_naver_profile(access_token)
    email = profile.get("email")

    if not email:
        return JsonResponse({"message": "이메일을 가져올 수 없습니다."}, status=400)

    user = User.objects.filter(email=email).first()

    # 유저가 있다면 로그인
    if user:
        # 유저가 활성화 되지 않았으면 활성화
        if not user.is_active:
            user.is_active = True
            user.save()

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # 프론트로 토큰 전달
        frontend_url = settings.FRONTEND_URL
        return redirect(
            f"{frontend_url}/oauth/callback?access={access}&refresh={str(refresh)}"
        )

    # 유저가 없다면 프론트에서 닉네임 받아서 별도 API로 회원가입
    frontend_url = settings.FRONTEND_URL
    return redirect(
        f"{frontend_url}/oauth/callback?access_token={access_token}&oauth=naver"
    )


def get_naver_access_token(code, state):
    params = {
        "grant_type": "authorization_code",
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "code": code,
        "state": state,
    }

    response = requests.get(NAVER_TOKEN_URL, params=params)
    result = response.json()
    return result.get("access_token")


def get_naver_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(NAVER_PROFILE_URL, headers=headers)

    if response.status_code != 200:
        raise Http404

    result = response.json()
    return result.get("response")


class OAuthSignupView(APIView):
    def post(self, request):
        access_token = request.data.get("access_token")
        nickname = request.data.get("nickname")
        oauth = request.data.get("oauth")

        if oauth != "naver":
            return Response({"message": "지원하지 않는 소셜 로그인입니다."}, status=400)

        if not access_token or not nickname:
            return Response({"message": "필수 값이 누락되었습니다."}, status=400)

        profile = get_naver_profile(access_token)
        email = profile.get("email")

        if not email or User.objects.filter(email=email).exists():
            return Response({"message": "이미 가입된 이메일입니다."}, status=400)

        user = User(email=email, nickname=nickname, is_active=True)
        random_pw = User.objects.make_random_password()
        user.set_password(random_pw)
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "회원가입 성공",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=201,
        )
