from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import ImageUploadSerializer


class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 인증

    @swagger_auto_schema(
        tags=["이미지"],
        operation_summary="이미지 업로드",
        operation_description="이미지를 업로드하고 썸네일을 생성합니다.",
        request_body=ImageUploadSerializer,
        responses={
            201: openapi.Response(
                description="업로드 성공",
                examples={
                    "application/json": {
                        "image_url": "https://example.com/media/uploads/original.webp",
                        "thumbnail_url": "https://example.com/media/uploads/thumb.webp",
                        "public_id": "abcdef123456",
                    }
                },
            ),
            400: "유효하지 않은 요청",
        },
    )
    def post(self, request):
        serializer = ImageUploadSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            image = serializer.save()
            return Response(
                {
                    "image_url": image.image_url,
                    "thumbnail_url": image.get_thumbnail_url(),
                    "public_id": image.public_id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["이미지"],
        operation_summary="이미지 수정",
        operation_description="기존 이미지들 삭제 후 새로운 이미지 등록",
        request_body=ImageUploadSerializer,
        responses={
            200: openapi.Response(
                description="수정 성공",
                examples={
                    "application/json": {
                        "image_url": "https://example.com/media/uploads/resized.webp",
                        "thumbnail_url": "https://example.com/media/uploads/thumb.webp",
                        "public_id": "abcdef123456",
                    }
                },
            ),
            400: "잘못된 요청",
        },
    )
    def patch(self, request):
        serializer = ImageUploadSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            image = serializer.update(None, serializer.validated_data)
            return Response(
                {
                    "image_url": image.image_url,
                    "thumbnail_url": image.get_thumbnail_url(),
                    "public_id": image.public_id,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["이미지"],
        operation_summary="이미지 삭제",
        operation_description="업로드된 이미지를 삭제합니다.",
        request_body=ImageUploadSerializer,
        responses={
            200: openapi.Response(
                description="삭제 성공", examples={"application/json": {"deleted": 1}}
            ),
            400: "삭제 실패 또는 잘못된 요청",
        },
    )
    def delete(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            deleted_count = serializer.delete()
            return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
