from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

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
        is_deleted (bool): 삭제 여부
        deleted_at (datetime): 삭제 시간
        deleted_by (User): 삭제한 사용자
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='deleted_posts'
    )

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
  
    def soft_delete(self, user):
        """
        게시물을 소프트 삭제합니다.
        
        Args:
            user (User): 삭제를 수행하는 사용자
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """삭제된 게시물을 복구합니다."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class Comment(models.Model):
    """
    댓글 모델
    
    Attributes:
        post (Post): 연결된 게시물
        author (User): 작성자
        content (str): 댓글 내용
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        is_deleted (bool): 삭제 여부
        deleted_at (datetime): 삭제 시간
        deleted_by (User): 삭제한 사용자
        parent (Comment): 부모 댓글 (대댓글인 경우)
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='deleted_comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]
        verbose_name = '댓글'
        verbose_name_plural = '댓글들'

    def __str__(self):
        """댓글의 문자열 표현을 반환합니다."""
        return f"{self.author.username} - {self.content[:20]}"

    def soft_delete(self, user):
        """
        댓글을 소프트 삭제합니다.
        
        Args:
            user (User): 삭제를 수행하는 사용자
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """삭제된 댓글을 복구합니다."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])