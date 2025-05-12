from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.image.models import Image
from apps.image.utils import delete_from_cloudinary, upload_to_cloudinary


class ImageUploadSerializer(serializers.ModelSerializer):
    model = serializers.CharField(write_only=True)
    object_id = serializers.IntegerField(write_only=True)
    image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Image
        fields = [
            "image_url",
            "public_id",
            "uploaded_at",
            "model",
            "object_id",
            "image",
        ]
        read_only_fields = ["image_url", "public_id", "uploaded_at"]

    def validate(self, data):
        try:
            data["content_type"] = ContentType.objects.get(model=data["model"].lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({"model": "유효하지 않은 모델입니다."})
        return data

    def create(self, validated_data):
        image_file = self.context["request"].FILES.get("image")
        if not image_file:
            raise serializers.ValidationError({"image": "이미지 파일이 필요합니다."})

        image_url, public_id = upload_to_cloudinary(
            image_file, folder=validated_data["model"]
        )

        return Image.objects.create(
            image_url=image_url,
            public_id=public_id,
            content_type=validated_data["content_type"],
            object_id=validated_data["object_id"],
        )

    def update(self, instance, validated_data):
        """
        기존 이미지들 삭제 후 새로운 이미지 등록
        """
        content_type = validated_data["content_type"]
        object_id = validated_data["object_id"]

        # 기존 이미지 삭제
        existing_images = Image.objects.filter(
            content_type=content_type, object_id=object_id
        )
        for image in existing_images:
            delete_from_cloudinary(image.public_id)
        existing_images.delete()

        # 새로 업로드
        return self.create(validated_data)

    # def update(self, instance, validated_data):
    #     """
    #     기존 이미지와 비교해서 diff 업데이트 수행
    #     - 유지: 요청에 포함된 기존 이미지
    #     - 삭제: 요청에서 빠진 기존 이미지
    #     - 추가: 요청에 새로 포함된 이미지
    #     """
    #     content_type = validated_data["content_type"]
    #     object_id = validated_data["object_id"]
    #     new_images_data = validated_data["images"]  # [{image, public_id, ...}, ...]
    #
    #     new_public_ids = {img["public_id"] for img in new_images_data}
    #     existing_images = Image.objects.filter(content_type=content_type, object_id=object_id)
    #
    #     # 삭제 대상: 기존에는 있었지만 요청에는 없는 public_id
    #     for image in existing_images:
    #         if image.public_id not in new_public_ids:
    #             delete_from_cloudinary(image.public_id)
    #             image.delete()
    #
    #     # 추가 대상: 요청에는 있지만 기존에는 없는 public_id
    #     existing_public_ids = {img.public_id for img in existing_images}
    #     for image_data in new_images_data:
    #         if image_data["public_id"] not in existing_public_ids:
    #             Image.objects.create(
    #                 image=image_data["image"],  # 또는 image_url 등
    #                 public_id=image_data["public_id"],
    #                 content_type=content_type,
    #                 object_id=object_id,
    #             )
    #
    #     # 최종 결과: object에 연결된 최신 이미지들 중 하나 리턴 (대표 이미지 등)
    #     return Image.objects.filter(content_type=content_type, object_id=object_id).first()

    def delete(self):
        """
        해당 모델 + object_id의 이미지 전부 삭제
        """
        validated_data = self.validated_data
        content_type = validated_data["content_type"]
        object_id = validated_data["object_id"]

        images = Image.objects.filter(content_type=content_type, object_id=object_id)
        for image in images:
            delete_from_cloudinary(image.public_id)
        count, _ = images.delete()
        return count
