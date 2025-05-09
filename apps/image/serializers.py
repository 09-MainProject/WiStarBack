from rest_framework import serializers
from .models import Image

class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "image", "content_type", "object_id"]

    def save(self, **kwargs):
        request = self.context.get("request")
        return super().save(request=request, **kwargs)