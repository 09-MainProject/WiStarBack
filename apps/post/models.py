from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    """
    게시물 모델

    Attributes:
        title (str): 게시물 제목
        content (str): 게시물 내용
        image_url (str): 게시물 이미지 URL
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        views (int): 조회수
        author (User): 작성자
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
        verbose_name = '게시물'
        verbose_name_plural = '게시물들'

    def __str__(self):
        """게시물의 문자열 표현을 반환합니다."""
        return self.title

    def increase_views(self):
        """조회수를 1 증가시킵니다."""
        self.views += 1
        self.save(update_fields=['views'])