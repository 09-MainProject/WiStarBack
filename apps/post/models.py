from io import BytesIO

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from apps.like.models import Like
from apps.user.models import User

from .utils import process_image

User = get_user_model()


class Post(models.Model):
    """
    게시물 모델

    Attributes:
        title (str): 게시물 제목
        content (str): 게시물 내용
        image (ImageField): 게시물 이미지
        image_url (str): 게시물 이미지 URL
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        views (int): 조회수
        author (User): 작성자
        is_deleted (bool): 삭제 여부
        deleted_at (datetime): 삭제 시간
        deleted_by (User): 삭제한 사용자
        likes (ManyToManyField): 좋아요한 사용자들
    """

    title = models.CharField("제목", max_length=200)
    content = models.TextField("내용")
    image = models.ImageField(
        "이미지", upload_to="media/post_images/%Y/%m/%d/", blank=True, null=True
    )
    image_url = models.URLField("이미지 URL", max_length=500, blank=True, null=True)
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)
    views = models.PositiveIntegerField("조회수", default=0)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", verbose_name="작성자"
    )
    likes = GenericRelation(Like, related_query_name="post")
    is_deleted = models.BooleanField("삭제 여부", default=False)
    deleted_at = models.DateTimeField("삭제일", null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_posts",
        verbose_name="삭제자",
    )

    def save(self, *args, **kwargs):
        # 이미지 파일이 있는 경우
        if self.image and hasattr(self.image, "file"):
            processed_image = process_image(self.image)
            self.image.save(processed_image.name, processed_image, save=False)

        # 이미지 URL이 있는 경우
        elif self.image_url and not self.image:
            try:
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    # 이미지 다운로드 및 처리
                    image_file = BytesIO(response.content)
                    processed_image = process_image(image_file)
                    # 파일명 생성
                    filename = (
                        f"downloaded_{timezone.now().strftime('%Y%m%d_%H%M%S')}.webp"
                    )
                    # 이미지 필드에 저장
                    self.image.save(filename, processed_image, save=False)
            except Exception as e:
                print(f"이미지 URL 처리 중 오류 발생: {e}")

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "게시물"
        verbose_name_plural = "게시물"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        """게시물의 문자열 표현을 반환합니다."""
        return self.title

    def increase_views(self):
        """조회수를 1 증가시킵니다."""
        self.views += 1
        self.save(update_fields=["views"])

    def soft_delete(self, user):
        """
        게시물을 소프트 삭제합니다.

        Args:
            user (User): 삭제를 수행하는 사용자
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

    def restore(self):
        """삭제된 게시물을 복구합니다."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
