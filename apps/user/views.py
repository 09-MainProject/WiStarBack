from django.conf import settings
from django.core import signing
from django.core.signing import TimestampSigner, SignatureExpired
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from utils.email import send_email
from apps.user.models import User
from apps.user.serializers import RegisterSerializer, ProfileSerializer, ProfileUpdateSerializer, LogoutSerializer


class RegisterView(CreateAPIView):
    queryset =  User.objects.all() # Model
    serializer_class = RegisterSerializer # Serializer

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

        verify_url = f'{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}'

        # 이메일 전송 또는 콘솔 출력
        # if settings.DEBUG:
        #     print('[3DJBank] 이메일 인증 링크:', verify_url)
        #     # 응답에 verify_url 포함
        #     response_data = serializer.data
        #     response_data["verify_url"] = verify_url
        #
        #     return Response(response_data, status=status.HTTP_201_CREATED)

        subject = '[WiStar] 이메일 인증을 완료해주세요.'
        message = f'아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}'
        send_email(subject, message, user.email)

        if settings.DEBUG:
            # print('[WiStar] 이메일 인증 링크:', verify_url)
            # 응답에 verify_url 포함
            response_data = serializer.data
            response_data["verify_url"] = verify_url
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

def verify_email(request):
    code = request.GET.get('code', '')  # code가 없으면 공백으로 처리
    signer = TimestampSigner()
    try:
        # 3. 직렬화된 데이터를 역직렬화
        decoded_user_email = signing.loads(code)
        # 4. 타임스탬프 유효성 검사 포함하여 복호화
        email = signer.unsign(decoded_user_email, max_age = 60 * 5)  # 5분 설정

        # email = signer.unsign(code, max_age = 60 * 5)  # 5분 설정
    # except Exception as e:  # 이렇게 처리 많이 하지만 에러를 지정해서 하는게 제일 좋음.
    except (SignatureExpired):  # 시간 지나서 오류발생하면 오류처리
        return JsonResponse({'detail': '인증 링크가 만료되었습니다.'}, status=400)
    except Exception:
        return JsonResponse({'detail': '유효하지 않은 인증 코드입니다.'}, status=400)

    user = get_object_or_404(User, email=email, is_active=False)
    user.is_active = True
    user.save()

    return JsonResponse({'detail': '이메일 인증이 완료되었습니다.'}, status=200)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        tokens = response.data

        custom_response = {
            "code": 200,
            "message": "로그인 성공",
            "data": {
                "token_type": "bearer",
                "refresh": tokens.get("refresh"),
                "access": tokens.get("access")
            }
        }

        return Response(custom_response, status=status.HTTP_200_OK)

class LogoutAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
    serializer_class = LogoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "로그아웃되었습니다."}, status=status.HTTP_205_RESET_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({"detail": "Deleted successfully"}, status=status.HTTP_200_OK)


# 토큰 정보 확인
# https://jwt.io/