from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Like(models.Model):
    TYPE_CHOICES = (
        ("post", "Post"),
        ("comment", "Comment"),
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    object_id = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("type", "object_id", "user")
