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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("content_type", "object_id", "user")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "content_type", "object_id"]),
        ]
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요들"

    def __str__(self):
        """좋아요의 문자열 표현을 반환합니다."""
        return f"{self.user.username}의 {self.content_object} 좋아요"
