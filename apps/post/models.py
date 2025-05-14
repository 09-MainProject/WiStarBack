from io import BytesIO

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.image.models import Image
from apps.like.models import Like
from apps.user.models import User

## from utils.models import Image  # 임시 주석처리: image 앱 도입 전까지


User = get_user_model()


class Post(models.Model):
    """
    게시물 모델

    Attributes:
        title (str): 게시물 제목
        content (str): 게시물 내용
        image (GenericRelation): 게시물 이미지 관계
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        views (int): 조회수
        author (User): 작성자
        is_deleted (bool): 삭제 여부
        deleted_at (datetime): 삭제 시간
        deleted_by (User): 삭제한 사용자
        likes (ManyToManyField): 좋아요한 사용자들
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("작성자"),
    )
    title = models.CharField(max_length=200, verbose_name=_("제목"))
    content = models.TextField(verbose_name=_("내용"))
    image = GenericRelation(Image, related_query_name="post_image")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("생성일"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("수정일"))
    views = models.PositiveIntegerField(default=0, verbose_name=_("조회수"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("삭제여부"))
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_posts",
    )
    likes = GenericRelation(
        Like, related_query_name="post_likes", verbose_name="좋아요"
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("게시물")
        verbose_name_plural = _("게시물")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        """게시물의 문자열 표현을 반환합니다."""
        return f"{self.author.nickname}의 게시물: {self.title}"

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
