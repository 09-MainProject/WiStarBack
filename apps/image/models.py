from pathlib import Path

from PIL import features
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image as PilImage
from io import BytesIO
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse


class Image(models.Model):
    # 실제 이미지 파일 (upload_to는 S3 업로드 시에도 사용됨)
    # image는 ImageField이기 때문에 .url 속성을 호출하면 저장된 파일의 경로가 자동으로 완전한 URL을 반환
    image = models.ImageField('이미지', null=True, blank=True, upload_to='uploads/%Y/%m/%d')
    thumbnail = models.ImageField('썸네일', null=True, blank=True, upload_to="uploads/%Y/%m/%d/thumbnail")

    # GenericForeignKey 구성 요소
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # 연결된 모델의 종류 (User, Post 등)
    object_id = models.PositiveIntegerField()  # 연결된 모델 인스턴스의 PK
    content_object = GenericForeignKey("content_type", "object_id")  # 위 둘을 합쳐 실제 객체처럼 동작하게 함

    # 추가 메타 정보 (선택)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # description = models.CharField(max_length=255, blank=True, null=True)  # 선택 설명

    # get_absolute_url은 보통 detail페이지
    # def get_absolute_url(self):
    #     return reverse('blog:detail', kwargs={'blog_pk':self.pk})

    # 이미지 가져오는 메서드
    def get_image_url(self):
        if self.image:
            return self.image.url
        # 이미지가 없으면 기본이미지 반환
        model = self.content_type.model
        if model == "user":
            return settings.DEFAULT_PROFILE_URL
        elif model == "post":
            return settings.DEFAULT_POST_URL
        return settings.DEFAULT_THUMBNAIL_URL  # 예외 대비 fallback

    # 썸네일 이미지 가져오는 메서드
    def get_thumbnail_image_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        elif self.image:
            return self.image.url
        # 이미지가 없으면 기본이미지 반환
        model = self.content_type.model
        if model == "user":
            return settings.DEFAULT_PROFILE_THUMBNAIL_URL
        elif model == "post":
            return settings.DEFAULT_POST_THUMBNAIL_URL
        return settings.DEFAULT_THUMBNAIL_URL  # 예외 대비 fallback

    def __str__(self):
        return f"{self.content_type} - {self.object_id} - {self.image.name}"

    class Meta:
        db_table = "image"
        verbose_name = "이미지"
        verbose_name_plural = "이미지 목록"
        ordering = ["-uploaded_at"]

    def save(self, *args, request=None, **kwargs):

        if self.image and request:
            # 프론트에서 GET 파라미터로 요청한 값 처리
            format = request.data.get("format", "WEBP").upper()
            quality = int(request.data.get("quality", 85))
            width = int(request.data.get("width"))
            height = int(request.data.get("height"))

            # 원본 이미지 변환 처리
            original = PilImage.open(self.image)
            original = original.convert("RGB")

            # width/height가 존재하면 리사이징
            if width and height:
                try:
                    original = original.resize((int(width), int(height)))
                except ValueError:
                    pass  # 값이 잘못되었으면 무시하고 원본 사용

            # 변환된 이미지 저장
            temp_image = BytesIO()
            original.save(temp_image, format=format, quality=quality)
            temp_image.seek(0)

            original_stem = Path(self.image.name).stem
            original_filename = f"{original_stem}.{format.lower()}"
            self.image.save(original_filename, ContentFile(temp_image.read()), save=False)
            temp_image.close()

            # 썸네일 고정 사이즈 생성
            thumbnail = original.copy()
            thumbnail.thumbnail((300, 300))

            # 변환된 이미지 저장
            temp_thumb = BytesIO()
            thumbnail_filename = f"{original_stem}_thumb.{format.lower()}"
            thumbnail.save(temp_thumb, format=format, quality=quality)
            temp_thumb.seek(0)

            self.thumbnail.save(thumbnail_filename, ContentFile(temp_thumb.read()), save=False)
            temp_thumb.close()

        return super().save(*args, **kwargs)

# BytesIO()는 Python의 표준 라이브러리 io 모듈에서 제공하는 메모리 기반의 이진 스트림 객체.
# 쉽게 말해, 파일처럼 쓸 수 있는 메모리 상의 버퍼
# 임시로 디스크에 저장하지 않고 이미지 데이터를 처리

# GenericForeignKey는 Django의 ContentTypes 프레임워크에서 제공하는 기능으로,
# **한 모델이 여러 다른 모델(Post, User 등)과 동적으로 관계를 맺을 수 있도록 해주는 "다형적 외래키(polymorphic foreign key)"**입니다.
#
# CREATE TABLE image (
#     id               BIGINT PRIMARY KEY,
#     image            VARCHAR, -- 업로드된 이미지 경로
#     uploaded_at      DATETIME,
#     content_type_id  INTEGER,  -- 연결된 모델의 ID (예: post, user 등)
#     object_id        INTEGER   -- 연결된 모델의 실제 인스턴스 PK
# );
#
# image 테이블
# id    image                       content_type_id    object_id
# 1     uploads/2025/05/09/a.jpg    7 (Post)           12
# 2     uploads/2025/05/09/b.jpg    3 (User)           4
#
# contenttype 테이블 (이미지 테이블의 content_type_id와 연결)
# id  app_label  model
# 3   user       user
# 7   post       post
#
# 2024/4/23일
# blog/2024/4/23/이미지파일.jpg
# ImageField, FieldField와 같은데 이미지만 업로드하게 되어있다.
# varchar => 경로만 저장을 함
# 이미지 필드를 사용하기 위해 pillow설  poetry add pillow

# models.CASCATE => 같이 삭제 => 유저 삭제시 같이 블로그도 같이 삭제
# models.PROTECT => 삭제가 불가능함 => 유저를 삭제하려고 할 때 블로그가 있으면 유저 삭제가 불가능 (기본값)
# models.SET_NULL => 널 값을 넣음 => 유저 삭제시 블로그의 author가 Null이 됨.
