from django.conf import settings
from django.core import signing
from django.core.signing import SignatureExpired, TimestampSigner
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_410_GONE,
)
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user.models import User
from apps.user.serializers import (
    LogoutSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
)
from utils.csrf import generate_csrf_token, validate_csrf_token
from utils.email import send_email
from utils.responses.user import (
    CSRF_INVALID_TOKEN,
    DELETE_SUCCESS,
    INVALID_SIGNATURE,
    LOGIN_SUCCESS,
    LOGOUT_SUCCESS,
    MISSING_REFRESH_TOKEN,
    SIGNATURE_EXPIRED,
    TOKEN_REFRESH_RESPONSE,
    VERIFY_EMAIL_SUCCESS,
)


# 회원 가입
class RegisterView(CreateAPIView):
    queryset = User.objects.all()  # Model
    serializer_class = RegisterSerializer  # Serializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 이메일 서명
        signer = TimestampSigner()

        # 1. 이메일에 서명
        signed_email = signer.sign(user.email)
        # 2. 서명된 이메일을 직렬화
        signed_code = signing.dumps(signed_email)

        # signed_code = signer.sign(user.email)

        verify_url = f"{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}"

        # 이메일 전송 또는 콘솔 출력
        # if settings.DEBUG:
        #     print('[3DJBank] 이메일 인증 링크:', verify_url)
        #     # 응답에 verify_url 포함
        #     response_data = serializer.data
        #     response_data["verify_url"] = verify_url
        #
        #     return Response(response_data, status=status.HTTP_201_CREATED)

        subject = "[WiStar] 이메일 인증을 완료해주세요."
        message = f"아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}"
        send_email(subject, message, user.email)

        if settings.DEBUG:
            # print('[WiStar] 이메일 인증 링크:', verify_url)
            # 응답에 verify_url 포함
            response_data = serializer.data
            response_data["verify_url"] = verify_url
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# 이메일 인증
# @csrf_exempt
def verify_email(request):
    code = request.GET.get("code", "")  # code가 없으면 공백으로 처리
    signer = TimestampSigner()
    try:
        # 3. 직렬화된 데이터를 역직렬화
        decoded_user_email = signing.loads(code)
        # 4. 타임스탬프 유효성 검사 포함하여 복호화
        email = signer.unsign(decoded_user_email, max_age=60 * 5)  # 5분 설정

        # email = signer.unsign(code, max_age = 60 * 5)  # 5분 설정
    # except Exception as e:  # 이렇게 처리 많이 하지만 에러를 지정해서 하는게 제일 좋음.
    except SignatureExpired:  # 시간 지나서 오류발생하면 오류처리
        return JsonResponse(SIGNATURE_EXPIRED, HTTP_410_GONE)
    except Exception:
        return Response(INVALID_SIGNATURE, HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, email=email, is_active=False)
    user.is_active = True
    user.save()

    return Response(VERIFY_EMAIL_SUCCESS, HTTP_200_OK)


# 로그인
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        tokens = response.data
        access_token = tokens.get("access")
        refresh_token = tokens.get("refresh")

        # 커스텀 CSRF 토큰 발급
        csrf_token = generate_csrf_token()
        # csrf_token = get_token(request)

        custom_response = LOGIN_SUCCESS
        custom_response["data"] = {
            "access_token": access_token,
            "csrf_token": csrf_token,
        }

        # Refresh Token을 HttpOnly 쿠키로 설정
        final_response = Response(custom_response, status=status.HTTP_200_OK)
        final_response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            # secure=True,        # HTTPS 환경에서만 전송
            secure=False,  # 로컬 개발 환경에 맞춰서 설정
            samesite="Lax",  # CSRF 공격 방지 설정
            path="/api/users/token",  # 필요한 경로에만 쿠키 사용
            max_age=60 * 60 * 24 * 1,  # 1일 (초 단위)
        )

        return final_response


# class LogoutAPIView(CreateAPIView):
#     # permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
#     permission_classes = []  # 인증 없이 호출 가능
#     serializer_class = LogoutSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"detail": "로그아웃되었습니다."}, status=status.HTTP_205_RESET_CONTENT)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 로그아웃
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = []  # 인증 없이 호출 가능

    def post(self, request, *args, **kwargs):

        # token = request.headers.get('X-CSRFToken')
        #
        # if not validate_csrf_token(token):
        #     raise PermissionDenied(CSRF_VALIDATION_FAILED)

        # 쿠키에서 Refresh Token 가져오기
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(MISSING_REFRESH_TOKEN, status=status.HTTP_401_UNAUTHORIZED)

        serializer = LogoutSerializer(data={"refresh_token": refresh_token})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 쿠키 삭제
        response = Response(LOGOUT_SUCCESS, status=status.HTTP_200_OK)
        response.delete_cookie(
            "refresh_token", path="/api/users/token"
        )  # Path 일치해야 함

        return response


# 엑세스 토큰 리프레시
class CustomTokenRefreshView(APIView):
    def post(self, request, *args, **kwargs):
        # CSRF 토큰 검증
        csrf_token = request.headers.get("X-CSRFToken")
        if not csrf_token or not validate_csrf_token(csrf_token):
            return Response(CSRF_INVALID_TOKEN, HTTP_403_FORBIDDEN)

        # 리프레시 토큰 쿠키에서 가져오기
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(MISSING_REFRESH_TOKEN, HTTP_401_UNAUTHORIZED)

        # SimpleJWT Serializer로 Access Token 재발급
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        new_access_token = serializer.validated_data.get("access")

        # 새로운 커스텀 CSRF 토큰 발급 (선택)
        new_csrf_token = generate_csrf_token()

        # 새로운 리프레시 토큰이 있다면 (ROTATE 설정 시)
        new_refresh_token = serializer.validated_data.get("refresh")

        # 응답 데이터 구성
        custom_response = TOKEN_REFRESH_RESPONSE
        custom_response["data"] = {
            "access_token": new_access_token,
            "csrf_token": new_csrf_token,
        }

        # 최종 응답
        final_response = Response(custom_response, status=status.HTTP_200_OK)

        # 새 리프레시 토큰이 있을 때만 쿠키에 다시 설정
        if new_refresh_token:
            final_response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=False,  # 로컬 개발환경
                samesite="Lax",
                path="/api/users/token",
                max_age=60 * 60 * 24 * 1,
            )

        return final_response


# 유저 수정
class ProfileView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    # serializer_class = UserMeReadSerializer
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 인증

    def get_object(self):
        # DRF 기본 동작
        # URL 통해 넘겨 받은 pk를 통해 queryset에 데이터를 조회
        # -> User.objects.all()
        return self.request.user  # 인증이 끝난 유저가 들어감.

    def get_serializer_class(self):
        # HTTP 메소드 별로 다른 Serializer 적용
        # -> 각 요청마다 입/출력에 사용되는 데이터의 형식이 다르기 때문

        if self.request.method == "GET":
            return ProfileSerializer

        elif self.request.method == "PATCH":
            return ProfileUpdateSerializer

        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):

        user = self.get_object()
        user.delete()
        return Response(DELETE_SUCCESS, status=status.HTTP_200_OK)


# 토큰 정보 확인
# https://jwt.io/
