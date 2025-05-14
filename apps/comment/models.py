from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.like.models import Like
from apps.post.models import Post
from apps.user.models import User

User = get_user_model()


class Comment(models.Model):
    """
    댓글 및 대댓글 모델
    - parent가 null이면 일반 댓글, 값이 있으면 대댓글
    """

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("게시글"),
        null=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("작성자"),
    )
    content = models.TextField(verbose_name=_("내용"))
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_comments",
        verbose_name=_("부모 댓글"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("생성일"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("수정일"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("삭제여부"))
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_comments",
    )
    likes = GenericRelation(Like, related_query_name="comment_likes", verbose_name="좋아요")

    class Meta:
        verbose_name = _("댓글")
        verbose_name_plural = _("댓글")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["post", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["parent", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.author.username}의 댓글: {self.content[:20]}"

    def soft_delete(self, user):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    @property
    def likes_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter(id=user.id).exists()

    @property
    def replies_count(self):
        return self.child_comments.count()

    def get_replies(self):
        return self.child_comments.filter(is_deleted=False).order_by("created_at")
