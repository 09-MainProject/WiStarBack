from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


class Like(models.Model):
    """
    좋아요 모델

    Attributes:
        user (User): 좋아요를 누른 사용자
        content_type (ContentType): 좋아요 대상의 ContentType
        object_id (int): 좋아요 대상의 ID
        content_object (GenericForeignKey): 좋아요 대상 객체
        created_at (datetime): 생성 시간
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="사용자",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="콘텐츠 타입",
        null=True,
    )
    object_id = models.PositiveIntegerField(verbose_name="객체 ID", null=True)
    content_object = GenericForeignKey("content_type", "object_id")
    post = models.ForeignKey(
        "post.Post",
        on_delete=models.CASCADE,
        related_name="post_likes",
        verbose_name="게시글",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요"
        unique_together = ["user", "content_type", "object_id"]

    def __str__(self):
        """좋아요의 문자열 표현을 반환합니다."""
        return f"{self.user.username}의 {self.content_object} 좋아요"
