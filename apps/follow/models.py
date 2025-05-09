from django.contrib.auth import get_user_model
from django.db import models

from apps.idol.models import Idol

User = get_user_model()

# 프로젝트에서 기본 AbstractUser 대신 커스텀 사용자 모델을 정의했다면,
# django.contrib.auth.models.User를 직접 import하면 잘못된 모델을 참조함.
# 반면 get_user_model()은 설정된 사용자 모델을 동적으로 반환.


class Follow(models.Model):
    """
    팔로우 모델

    Attributes:
        user (User): 팔로우를 누른 사용자
        idol (Idol): 팔로우한 아이돌
        created_at (datetime): 생성 시간
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followings")
    idol = models.ForeignKey(Idol, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField("생성일자", auto_now_add=True)

    class Meta:
        unique_together = ("user", "idol")
        db_table = "follow"
        verbose_name = "팔로우"
        verbose_name_plural = f"{verbose_name} 목록"
        ordering = ["-created_at"]

    def __str__(self):
        """팔로우의 문자열 표현을 반환."""
        return f"{self.user.username}가 {self.idol}을 팔로우"
