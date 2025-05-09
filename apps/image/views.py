from django.shortcuts import render

from .models import Image
from .serializers import ImageUploadSerializer
from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

# class ImageUploadView(APIView):
#     def post(self, request):
#         serializer = ImageUploadSerializer(data=request.data)
#         if serializer.is_valid():
#             instance = serializer.save()
#             return Response({
#                 "message": "이미지 업로드 성공",
#                 "image_url": request.build_absolute_uri(instance.image.url)
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 프론트 요청 예시
# const formData = new FormData();
# formData.append("image", selectedFile);
# formData.append("content_type", 7);  // 예: post
# formData.append("object_id", 12);    // 해당 Post의 ID
#
# fetch("/api/images/", {
#   method: "POST",
#   body: formData,
# });

class ImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        model_name = request.data.get("content_type")
        object_id = request.data.get("object_id")
        image_file = request.FILES.get("image")

        if not (model_name and object_id and image_file):
            return Response({"error": "필수 데이터 누락"}, status=400)

        try:
            content_type = ContentType.objects.get(model=model_name.lower())
            target_model = content_type.get_object_for_this_type(pk=object_id)
        except ContentType.DoesNotExist:
            return Response({"error": "존재하지 않는 모델"}, status=400)
        except target_model.DoesNotExist:
            return Response({"error": "해당 객체를 찾을 수 없습니다"}, status=404)

        # 이미지 생성 및 저장
        image = Image.objects.create(
            image=image_file,
            content_object=target_model
        )
        image.save(request=request)  # 썸네일 생성 포함

        return Response({
            "message": "이미지 업로드 성공",
            "image_url": image.image.url,
            "thumbnail_url": image.thumbnail.url if image.thumbnail else None
        }, status=201)

# [1단계] 이미지 업로드 (/api/images/)
#
# content_type=user, object_id=유저 ID와 함께 이미지 전송
#
# 응답: 이미지 URL + 썸네일 URL
#
# [2단계] 프로필 수정 요청 (/api/users/me/)
#
# name, nickname, bio, etc...
#


# {
#     "message": "이미지 업로드 성공",
#     "image_url": "https://s3.amazonaws.com/.../uploads/2025/05/09/a.webp",
#     "thumbnail_url": "https://s3.amazonaws.com/.../uploads/2025/05/09/a_thumb.webp"
# }